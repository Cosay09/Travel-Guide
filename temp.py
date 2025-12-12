# at top of temp.py (imports)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from itinerary_utils import (
    compute_trip_estimate,
    ensure_saved_itineraries_table,
    haversine_km,
    transport_cost_km_mode,
    accommodation_cost,
    food_cost,
    resolve_city_coords
)
from utils.itinerary_presets import get_preset_for_destination, preset_to_plan

import customtkinter as ctk
import sqlite3
import hashlib
import os
import json
from PIL import Image, ImageTk
from config import DB_PATH
import webbrowser
import math

ATTRACTIONS_PATH = "data/attractions_augmented.json"


def export_itinerary_to_pdf(plan: dict, path: str, title: str = "Itinerary"):
    """
    plan: { "requested": {...}, "costs": {...}, "plan": [{ "day":1, "stops":[{time,name,desc,...}, ...]}, ...] }
    path: output .pdf path (string)
    """
    # If user provided only a plan list, accept that
    if isinstance(plan, dict) and "plan" in plan:
        plan_list = plan["plan"]
    elif isinstance(plan, list):
        plan_list = plan
    else:
        raise ValueError("Invalid plan shape for PDF export")

    # Register custom font if present (use for Bangla if you add a TTF)
    # You can place a TTF in data/fonts/ and set FONT_PATH to it.
    FONT_PATH = os.path.join("data", "fonts", "SolaimanLipi.ttf")  # change if needed
    REGISTERED_FONT = "Helvetica"
    try:
        if os.path.exists(FONT_PATH):
            pdfmetrics.registerFont(TTFont("Bangla", FONT_PATH))
            REGISTERED_FONT = "Bangla"
    except Exception:
        # fallback to default if font registration fails
        REGISTERED_FONT = "Helvetica"

    # Document setup: A4 portrait
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)

    styles = getSampleStyleSheet()
    # override/define styles
    styles.add(ParagraphStyle(name='TitleCenter', parent=styles['Title'],
                              alignment=TA_CENTER, fontName=REGISTERED_FONT, fontSize=18, leading=22))
    styles.add(ParagraphStyle(name='DayHeading', parent=styles['Heading2'],
                              fontName=REGISTERED_FONT, fontSize=14, leading=18, spaceAfter=6))
    styles.add(ParagraphStyle(name='StopName', parent=styles['Normal'],
                              fontName=REGISTERED_FONT, fontSize=12, leading=14, spaceAfter=2, leftIndent=6))
    styles.add(ParagraphStyle(name='StopDesc', parent=styles['Normal'],
                              fontName=REGISTERED_FONT, fontSize=11, leading=14, spaceAfter=8, leftIndent=12, textColor="#333333"))
    styles.add(ParagraphStyle(name='Meta', parent=styles['Normal'],
                              fontName=REGISTERED_FONT, fontSize=9, leading=11, textColor="#666666"))

    story = []
    # Title
    story.append(Paragraph(title, styles['TitleCenter']))
    story.append(Spacer(1, 6))

    # optional meta line (days, people)
    # If plan is the dict with requested info, try to show meta:
    if isinstance(plan, dict) and "requested" in plan:
        req = plan.get("requested", {})
        meta_text = f"{req.get('days','?')} days · {req.get('people','?')} people · {req.get('destination','')}"
        story.append(Paragraph(meta_text, styles['Meta']))
        story.append(Spacer(1, 6))

    # Render days
    for day in plan_list:
        day_num = day.get("day", None)
        if day_num is not None:
            story.append(Paragraph(f"Day {day_num}", styles['DayHeading']))
        else:
            story.append(Paragraph("Day", styles['DayHeading']))

        # stops
        stops = day.get("stops", [])
        if not stops:
            story.append(Paragraph("No suggested stops.", styles['StopDesc']))
        else:
            for stop in stops:
                time = stop.get("time", "")
                name = stop.get("name", "")
                desc = stop.get("desc", "") or stop.get("summary", "")
                # time + name bold line
                line = f"<b>{time} — {name}</b>"
                story.append(Paragraph(line, styles['StopName']))
                if desc:
                    story.append(Paragraph(desc, styles['StopDesc']))

        # small spacer between days
        story.append(Spacer(1, 8))

        # optional page break if story size large — SimpleDocTemplate will flow pages automatically

    # Build PDF
    doc.build(story)



def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()



def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()



def load_attractions():
    """Load attractions list from JSON file."""
    try:
        with open(ATTRACTIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except FileNotFoundError:
        print("attractions.json not found")
        return []
    except json.JSONDecodeError as e:
        print("Error reading attractions.json:", e)
        return []
    

def haversine_km(coord1, coord2):
    # coord = (lat, lon) in degrees
    R = 6371.0
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def open_google_maps_directions(origin_text, dest_text, origin_coords=None, dest_coords=None):
    """
    Compute distance (if coords available), open Google Maps directions for the two places.
    Returns distance_km (float) or None if coords missing.
    """
    # build google maps directions url (using textual query fallback)
    origin_q = origin_text or ""
    dest_q = dest_text or ""
    if origin_coords and dest_coords:
        # use "lat,lon" pairs to be precise
        origin_q = f"{origin_coords[0]},{origin_coords[1]}"
        dest_q = f"{dest_coords[0]},{dest_coords[1]}"
        distance = round(haversine_km(origin_coords, dest_coords), 2)
    else:
        distance = None

    url = f"https://www.google.com/maps/dir/{origin_q}/{dest_q}/"
    webbrowser.open(url)
    return distance


def load_content_from_file(path: str) -> str:
    """Load long text/blog content from .md or .txt file."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"⚠ Content file not found: {path}"
    except Exception as e:
        return f"⚠ Error loading content from {path}: {e}"



PAGES = (
    "Overview",
    "Top Attractions",
    "Itineraries",
    "Local Transportation",
    "Accommodation",
    "Food & Drink",
    "Practical Info",
    "Maps & Visuals",
    "Day Trips & Hidden Gems",
)



class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Travel Guide")
        self.geometry("1280x720")  # Good starting size
        self.minsize(1150, 650)    # Prevent layout collapse
        self.resizable(False, True) # Smooth resizing allowed


        ctk.set_appearance_mode("light")   # "dark" or "light"
        ctk.set_default_color_theme("blue")

        init_db()

        # start with login screen
        self.login_frame = LoginFrame(self, self.on_login_success)
        self.login_frame.pack(fill="both", expand=True)

    # ---- called when login/register/guest success ----
    def on_login_success(self, email, is_guest):
        self.user_email = email
        self.is_guest = is_guest

        # properly remove login frame
        self.login_frame.pack_forget()
        self.login_frame.update()
        self.login_frame.destroy()

        # now safely build main UI
        self.build_main_ui()

    # ---- build the actual app ----
    def build_main_ui(self):
        # sidebar state
        self.sidebar_visible = False
        self.sidebar_built = False

        # Topbar
        self.topbar = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.topbar.pack(side="top", fill="x")

        self.menu_btn = ctk.CTkButton(
            self.topbar, text="☰", width=40, command=self.toggle_sidebar
        )
        self.menu_btn.pack(side="left", padx=10, pady=8)

        self.title_lbl = ctk.CTkLabel(
            self.topbar,
            text=f"Travel Guide ({'Guest' if self.is_guest else self.user_email})",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_lbl.pack(side="left", padx=6)

        # Main body (use grid for stable left/right layout)
        self.body = ctk.CTkFrame(self, corner_radius=0)
        self.body.pack(side="top", fill="both", expand=True)

        # Make a 2-column grid: 0 = sidebar, 1 = content
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(1, weight=1)   # content column expands

        # Sidebar (initially created but hidden)
        self.sidebar = ctk.CTkScrollableFrame(self.body, width=220, corner_radius=0, fg_color="#0F172A")

        # Content (always present)
        self.content = ctk.CTkFrame(self.body, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")  # column 1 (right side)

        self.pages = {}
        self.show_page("Overview")  # show default page

        # navigation history (stack of page names)
        self.page_history = []
        self.current_page_name = None

        ensure_saved_itineraries_table()


    def build_sidebar(self):
        if getattr(self, "sidebar_built", False):
            return
        self.sidebar_built = True

        self.sidebar_buttons = {}

        # ----- Header (app title + user) -----
        header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(14, 8))

        ctk.CTkLabel(
            header,
            text="🌍 Travel Guide",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=f"Signed in as: {'Guest' if self.is_guest else self.user_email}",
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF",
        ).pack(anchor="w", pady=(2, 0))

        # separator line
        ctk.CTkFrame(
            self.sidebar, height=1, fg_color="#1F2937", corner_radius=0
        ).pack(fill="x", padx=12, pady=(4, 8))

        # icons per page
        page_icons = {
            "Overview": "🏠",
            "Top Attractions": "📍",
            "Itineraries": "🗓",
            "Local Transportation": "🚆",
            "Accommodation": "🏨",
            "Food & Drink": "🍛",
            "Practical Info": "ℹ",
            "Maps & Visuals": "🗺",
            "Day Trips & Hidden Gems": "✨",
        }

        # ----- Menu buttons -----
        for name in PAGES:
            icon = page_icons.get(name, "📄")
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}  {name}",
                anchor="w",
                height=36,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#1E293B",
                text_color="#E5E7EB",
                font=ctk.CTkFont(size=13),
                command=lambda n=name: self.show_page(n),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.sidebar_buttons[name] = btn
            
        # ----- Logout button directly after last option -----
        ctk.CTkButton(
            self.sidebar,
            text="⏏  Logout",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            text_color="white",
            height=34,
            corner_radius=8,
            command=self.logout,
        ).pack(fill="x", padx=12, pady=(10, 16))



    def highlight_sidebar(self, active_name: str):
        """Visually highlight the active page button."""
        if not hasattr(self, "sidebar_buttons"):
            return

        for name, btn in self.sidebar_buttons.items():
            if name == active_name:
                btn.configure(
                    fg_color="#2563EB",
                    text_color="white",
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color="#E5E7EB",
                )



    def toggle_sidebar(self):
        if self.sidebar_visible:
            # hide sidebar
            try:
                self.sidebar.grid_remove()
            except Exception:
                pass
            self.sidebar_visible = False
        else:
            # ensure sidebar buttons exist
            self.build_sidebar()
            # show sidebar in column 0 (left)
            self.sidebar.grid(row=0, column=0, sticky="ns")
            self.sidebar_visible = True


    def get_page(self, name):
        if name not in self.pages:
            if name == "Overview":
                self.pages[name] = OverviewPage(self.content)
            elif name == "Top Attractions":
                self.pages[name] = TopAttractionsPage(self.content)
            elif name == "Itineraries":
                self.pages[name] = ItinerariesPage(self.content)
            else:
                self.pages[name] = PlaceholderPage(self.content, name)

        return self.pages[name]

    def show_page(self, name, record_history: bool = True):
        # record currently shown page (if any) to allow "Back"
        if record_history and getattr(self, "current_page_name", None) and self.current_page_name != name:
            self.page_history.append(self.current_page_name)

        # Clear old widgets from the content frame
        for widget in self.content.winfo_children():
            widget.grid_remove()

        page = self.get_page(name)
        page.grid(row=0, column=0, sticky="nsew")

        # remember what is currently visible
        self.current_page_name = name

        # Make sure the page expands with the content area
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # highlight active button in sidebar (if built)
        if getattr(self, "sidebar_built", False):
            self.highlight_sidebar(name)


    def go_back(self):
        """Navigate to the previous page in the history stack (if any)."""
        if not getattr(self, "page_history", None):
            # nothing to go back to — fallback to Overview
            self.show_page("Overview", record_history=False)
            return

        prev = self.page_history.pop()
        # show previous page without adding current page back into history
        self.show_page(prev, record_history=False)



    def show_attraction_page(self, attraction):
        """Show full-page attraction detail inside main content area.

        Ensure the current page (e.g. 'Top Attractions') is saved into history
        so go_back() returns to it.
        """
        # Optional: close sidebar for better focus
        if getattr(self, "sidebar_visible", False):
            self.toggle_sidebar()

        # Record current page in history so Back returns here
        cur = getattr(self, "current_page_name", None)
        if cur:
            if not hasattr(self, "page_history"):
                self.page_history = []
            # Avoid pushing duplicate entries
            if not self.page_history or self.page_history[-1] != cur:
                self.page_history.append(cur)

        # Hide any current pages in content
        for widget in self.content.winfo_children():
            widget.grid_remove()

        # Create a fresh detail page (not cached)
        detail_key = f"Attraction:{attraction.get('name','unknown')}"
        # create the brochure/detail and show it
        detail_page = AttractionDetailPageBrochure(
            self.content,
            attraction,
            go_back_callback=self.go_back
        )
        detail_page.grid(row=0, column=0, sticky="nsew")

        # remember that we're now showing this "page"
        self.current_page_name = detail_key
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def logout(self):
        """Safely remove the main UI and return to login screen."""
        # Destroy main UI widgets if they exist
        for name in ("topbar", "body", "sidebar", "content"):
            if hasattr(self, name):
                widget = getattr(self, name)
                try:
                    widget.destroy()
                except Exception:
                    pass
                try:
                    delattr(self, name)
                except Exception:
                    pass

        # Clear pages cache if present
        if hasattr(self, "pages"):
            try:
                for p in list(self.pages.values()):
                    try:
                        p.destroy()
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                delattr(self, "pages")
            except Exception:
                pass

        # reset sidebar state
        self.sidebar_visible = False
        self.sidebar_built = False

        # remove any leftover attributes that could conflict
        for leftover in ("menu_btn", "title_lbl"):
            if hasattr(self, leftover):
                try:
                    getattr(self, leftover).destroy()
                except Exception:
                    pass
                try:
                    delattr(self, leftover)
                except Exception:
                    pass

        # Create and show login frame in the same window
        self.login_frame = LoginFrame(self, self.on_login_success)
        self.login_frame.pack(fill="both", expand=True)



class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.on_login_success = on_login_success
        self.configure(fg_color="#E5E7EB")  # soft gray background
        self.build_ui()

    def build_ui(self):
        # ===== Main 2-column layout =====
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=3)
        container.grid_columnconfigure(1, weight=4)

        # ---------- LEFT: Hero / branding ----------
        left = ctk.CTkFrame(
            container,
            corner_radius=20,
            fg_color="#0F172A"
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        ctk.CTkLabel(
            left,
            text="🌍 Travel Guide",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="white"
        ).pack(anchor="w", padx=24, pady=(24, 8))

        ctk.CTkLabel(
            left,
            text="Discover beaches, hills, heritage sites\nand hidden gems across Bangladesh.",
            font=ctk.CTkFont(size=14),
            text_color="#E5E7EB",
            justify="left"
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # Little feature bullets
        bullet_frame = ctk.CTkFrame(left, fg_color="transparent")
        bullet_frame.pack(anchor="w", padx=20, pady=(0, 20))

        def bullet(text):
            row = ctk.CTkFrame(bullet_frame, fg_color="transparent")
            row.pack(anchor="w", pady=2)
            ctk.CTkLabel(
                row,
                text="•",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#38BDF8",
                width=10
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=text,
                font=ctk.CTkFont(size=12),
                text_color="#E5E7EB",
                justify="left"
            ).pack(side="left")

        bullet("Save time with curated top attractions.")
        bullet("Plan trips with itineraries and local tips.")
        bullet("All your info in one simple interface.")

        ctk.CTkLabel(
            left,
            text="Log in or continue as guest\nto start exploring.",
            font=ctk.CTkFont(size=12),
            text_color="#9CA3AF",
            justify="left"
        ).pack(anchor="w", padx=24, pady=(0, 20))

        # ---------- RIGHT: Login card ----------
        right = ctk.CTkFrame(
            container,
            corner_radius=20,
            fg_color="#FFFFFF"
        )
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

        # Inner padding frame
        inner = ctk.CTkFrame(right, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=26, pady=26)

        ctk.CTkLabel(
            inner,
            text="Welcome back",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#111827"
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            inner,
            text="Sign in to continue planning your journey.",
            font=ctk.CTkFont(size=13),
            text_color="#6B7280"
        ).pack(anchor="w", pady=(0, 14))

        # Email entry
        self.email_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Email address",
            width=320,
            font=ctk.CTkFont(size=14)
        )
        self.email_entry.pack(pady=(8, 8))

        # Password entry
        self.password_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Password",
            show="*",
            width=320,
            font=ctk.CTkFont(size=14)
        )
        self.password_entry.pack(pady=(0, 4))

        # Bind Enter to login
        self.email_entry.bind("<Return>", lambda event: self.login())
        self.password_entry.bind("<Return>", lambda event: self.login())

        # Small hint under password
        ctk.CTkLabel(
            inner,
            text="Use the same account to access your saved plans later.",
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF"
        ).pack(anchor="w", pady=(0, 10))

        # Buttons
        ctk.CTkButton(
            inner,
            text="Log in",
            height=36,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.login
        ).pack(fill="x", pady=(4, 6))

        ctk.CTkButton(
            inner,
            text="Create a new account",
            height=32,
            fg_color="#F3F4F6",
            hover_color="#E5E7EB",
            text_color="#111827",
            command=self.open_register
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            inner,
            text="Continue as Guest",
            height=32,
            fg_color="#111827",
            hover_color="#020617",
            text_color="white",
            command=self.login_guest
        ).pack(fill="x", pady=(0, 10))

        # Message label for errors
        self.message = ctk.CTkLabel(inner, text="", text_color="red")
        self.message.pack(anchor="w", pady=(4, 0))

    # ==== logic stays exactly the same ====
    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not email or not password:
            self.message.configure(text="Please fill all fields")
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE email=?", (email,))
        result = cur.fetchone()
        conn.close()

        if result and result[0] == hash_password(password):
            self.on_login_success(email, is_guest=False)
        else:
            self.message.configure(text="Invalid email or password")

    def login_guest(self):
        self.on_login_success("guest", is_guest=True)

    def open_register(self):
        self.destroy()
        RegisterFrame(self.master, self.on_login_success).pack(fill="both", expand=True)



class FastScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master=None, scroll_speed: int = 3, **kwargs):
        """
        scroll_speed: how many "steps" per wheel notch.
        1 = default-ish, 3 = faster, 5 = very fast.
        """
        self._scroll_speed = scroll_speed
        super().__init__(master, **kwargs)

    def _mouse_wheel(self, event):
        """Override CTkScrollableFrame default wheel speed (Windows)."""
        # On Windows, event.delta is typically ±120 per notch
        if event.delta != 0:
            steps = int(-event.delta / 120 * self._scroll_speed)
            self._parent_canvas.yview_scroll(steps, "units")



class RegisterFrame(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.on_login_success = on_login_success
        self.configure(fg_color="#E5E7EB")  # same soft bg as login
        self.show_password = False
        self.build_ui()

    def build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Center card
        card = ctk.CTkFrame(
            container,
            corner_radius=20,
            fg_color="#FFFFFF",
        )
        card.grid(row=0, column=0, sticky="nsew", padx=80, pady=20)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=26, pady=26)

        # Use a clean grid inside the card
        inner.grid_columnconfigure(0, weight=1)

        row = 0

        # ----- Title -----
        ctk.CTkLabel(
            inner,
            text="Create a new account",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#111827",
        ).grid(row=row, column=0, sticky="w", pady=(0, 4))
        row += 1

        ctk.CTkLabel(
            inner,
            text="Sign up to save your plans and come back to them anytime.",
            font=ctk.CTkFont(size=13),
            text_color="#6B7280",
        ).grid(row=row, column=0, sticky="w", pady=(0, 16))
        row += 1

        # ----- Full name -----
        self.name_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Full name",
            width=320,
            font=ctk.CTkFont(size=14),
        )
        self.name_entry.grid(row=row, column=0, sticky="ew", pady=(4, 8))
        row += 1

        # ----- Email -----
        self.email_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Email address",
            width=320,
            font=ctk.CTkFont(size=14),
        )
        self.email_entry.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        row += 1

        # ----- Password row: entry + toggle, aligned with others -----
        pass_row = ctk.CTkFrame(inner, fg_color="transparent")
        pass_row.grid(row=row, column=0, sticky="ew", pady=(0, 4))
        pass_row.grid_columnconfigure(0, weight=1)
        pass_row.grid_columnconfigure(1, weight=0)

        self.password_entry = ctk.CTkEntry(
            pass_row,
            placeholder_text="Password",
            show="*",
            font=ctk.CTkFont(size=14),
        )
        self.password_entry.grid(row=0, column=0, sticky="ew")

        self.toggle_btn = ctk.CTkButton(
            pass_row,
            text="Show",
            width=60,
            height=30,
            fg_color="#E5E7EB",
            hover_color="#D1D5DB",
            text_color="#111827",
            command=self.toggle_password_visibility,
        )
        self.toggle_btn.grid(row=0, column=1, padx=(6, 0))

        row += 1

        # ----- Confirm password -----
        self.confirm_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Confirm password",
            show="*",
            width=320,
            font=ctk.CTkFont(size=14),
        )
        self.confirm_entry.grid(row=row, column=0, sticky="ew", pady=(4, 6))
        row += 1

        # ----- Hint -----
        ctk.CTkLabel(
            inner,
            text="Use at least 6 characters. Passwords must match.",
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF",
        ).grid(row=row, column=0, sticky="w", pady=(0, 10))
        row += 1

        # ----- Create account button -----
        ctk.CTkButton(
            inner,
            text="Create account",
            height=36,
            fg_color="#16A34A",
            hover_color="#15803D",
            text_color="white",
            command=self.register,
        ).grid(row=row, column=0, sticky="ew", pady=(4, 8))
        row += 1

        # ----- Back to login -----
        ctk.CTkButton(
            inner,
            text="← Back to login",
            height=32,
            fg_color="#F3F4F6",
            hover_color="#E5E7EB",
            text_color="#111827",
            command=self.back_to_login,
        ).grid(row=row, column=0, sticky="ew")
        row += 1

        # ----- Message label (errors / success) -----
        self.message = ctk.CTkLabel(inner, text="", text_color="red")
        self.message.grid(row=row, column=0, sticky="w", pady=(8, 0))

    def toggle_password_visibility(self):
        self.show_password = not self.show_password
        char = "" if self.show_password else "*"
        self.password_entry.configure(show=char)
        self.confirm_entry.configure(show=char)
        self.toggle_btn.configure(text="Hide" if self.show_password else "Show")

    def register(self):
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm = self.confirm_entry.get().strip()

        if not name or not email or not password or not confirm:
            self.message.configure(text="All fields are required", text_color="red")
            return

        if len(password) < 6:
            self.message.configure(text="Password must be at least 6 characters", text_color="red")
            return

        if password != confirm:
            self.message.configure(text="Passwords do not match", text_color="red")
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users VALUES (?, ?, ?)",
                (email, name, hash_password(password)),
            )
            conn.commit()
            self.message.configure(
                text="Registration successful! You can log in now.",
                text_color="green",
            )
        except sqlite3.IntegrityError:
            self.message.configure(text="Email already registered", text_color="red")
        finally:
            conn.close()

    def back_to_login(self):
        self.destroy()
        LoginFrame(self.master, self.on_login_success).pack(fill="both", expand=True)



class OverviewPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        # ===== HERO BANNER =====
        hero = ctk.CTkFrame(self, corner_radius=0, fg_color="#0078D4")
        hero.pack(fill="x", padx=0, pady=0)

        title = ctk.CTkLabel(
            hero,
            text="🌍 Discover Bangladesh",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white",
        )
        title.pack(pady=(18, 4))

        subtitle = ctk.CTkLabel(
            hero,
            text="Your personal travel companion for beaches, hills, history and hidden gems.",
            font=ctk.CTkFont(size=14),
            text_color="white",
            wraplength=800,
        )
        subtitle.pack(pady=(0, 14))

        # ===== MAIN CONTENT AREA =====
        main = ctk.CTkFrame(self, fg_color="#F3F6FB")  # soft background
        main.pack(fill="both", expand=True, padx=0, pady=0)

        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=2)
        main.grid_columnconfigure(1, weight=1)

        # ---------- LEFT: Quick actions & steps ----------
        left = ctk.CTkFrame(main, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=(15, 20))

        ctk.CTkLabel(
            left,
            text="Start exploring in a few taps",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#0F172A",
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            left,
            text="Jump into the most useful sections of the guide.",
            font=ctk.CTkFont(size=13),
            text_color="#334155",
        ).pack(anchor="w", pady=(0, 12))

        # Quick action buttons
        actions = ctk.CTkFrame(left, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 12))

        def go(page_name: str):
            app = self.winfo_toplevel()
            app.show_page(page_name)

        ctk.CTkButton(
            actions,
            text="🏖  Explore Top Attractions",
            height=40,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="white",
            command=lambda: go("Top Attractions"),
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            actions,
            text="🧳  Plan with Itineraries",
            height=40,
            fg_color="#16A34A",
            hover_color="#15803D",
            text_color="white",
            command=lambda: go("Itineraries"),
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            actions,
            text="ℹ  Practical Travel Info",
            height=40,
            fg_color="#F97316",
            hover_color="#EA580C",
            text_color="white",
            command=lambda: go("Practical Info"),
        ).pack(fill="x", pady=4)

        # 4 colorful step cards
        steps_frame = ctk.CTkFrame(left, fg_color="transparent")
        steps_frame.pack(fill="both", expand=True, pady=(10, 0))

        steps_frame.grid_columnconfigure(0, weight=1)
        steps_frame.grid_columnconfigure(1, weight=1)

        self._create_step_card(
            steps_frame,
            row=0, col=0,
            emoji="📍",
            title="Pick a destination",
            text="Browse beaches, hills, forests and cities with photos and key highlights.",
            bg="#DBEAFE",
        )
        self._create_step_card(
            steps_frame,
            row=0, col=1,
            emoji="🗓",
            title="Shape your days",
            text="Use suggested 1–3 day plans or combine spots into your own trip.",
            bg="#DCFCE7",
        )
        self._create_step_card(
            steps_frame,
            row=1, col=0,
            emoji="🚆",
            title="Sort out logistics",
            text="Check transport options, timings and tips so you reach easily.",
            bg="#FEF3C7",
        )
        self._create_step_card(
            steps_frame,
            row=1, col=1,
            emoji="🍛",
            title="Taste & experience",
            text="Find must-try foods, cafés and local experiences near each place.",
            bg="#FFE4E6",
        )

        # ---------- RIGHT: Highlight / inspiration ----------
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=(15, 20))

        highlight = ctk.CTkFrame(right, corner_radius=18, fg_color="#0F172A")
        highlight.pack(fill="both", expand=False, pady=(0, 12))

        ctk.CTkLabel(
            highlight,
            text="Today’s Inspiration",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white",
        ).pack(anchor="w", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            highlight,
            text=(
                "Not sure where to begin?\n\n"
                "• Cox’s Bazar for endless beaches\n"
                "• Sajek for clouds & hills\n"
                "• Sundarbans for wildlife & rivers\n\n"
                "Open Top Attractions to dive deeper."
            ),
            justify="left",
            font=ctk.CTkFont(size=13),
            text_color="#E5E7EB",
        ).pack(anchor="w", padx=14, pady=(0, 12))

        ctk.CTkButton(
            highlight,
            text="View Top Attractions →",
            height=34,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="white",
            command=lambda: go("Top Attractions"),
        ).pack(anchor="w", padx=14, pady=(0, 14))

        # Small info card at bottom right
        tip = ctk.CTkFrame(right, corner_radius=14, fg_color="#E0F2FE")
        tip.pack(fill="x")

        ctk.CTkLabel(
            tip,
            text="Tip",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#0F172A",
        ).pack(anchor="w", padx=10, pady=(8, 0))

        ctk.CTkLabel(
            tip,
            text="You can always return here from the menu\nif you feel lost while exploring.",
            font=ctk.CTkFont(size=12),
            text_color="#1F2933",
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 8))

    def _create_step_card(self, parent, row, col, emoji, title, text, bg):
        """Small colorful card for the 4 steps."""
        card = ctk.CTkFrame(parent, corner_radius=14, fg_color=bg)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        parent.grid_rowconfigure(row, weight=1)

        ctk.CTkLabel(
            card,
            text=f"{emoji}  {title}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#111827",
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            card,
            text=text,
            font=ctk.CTkFont(size=12),
            justify="left",
            wraplength=260,
            text_color="#374151",
        ).pack(anchor="w", padx=10, pady=(0, 10))



class TopAttractionsPage(FastScrollableFrame):  # or ctk.CTkScrollableFrame
    def __init__(self, parent):
        super().__init__(parent, scroll_speed=4)   # if using FastScrollableFrame

        # ===== Header section =====
        header = ctk.CTkFrame(self, fg_color="#0078D4", corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            header,
            text="🏖 Top Attractions",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="white"
        ).pack(pady=16)

        # ===== Main area background =====
        container = ctk.CTkFrame(self, fg_color="#F3F6FB", corner_radius=0)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        # Load attractions data
        self.attractions = load_attractions()
        if not self.attractions:
            ctk.CTkLabel(container, text="No attractions found.").pack(pady=20)
            return

        # keep cached images alive: list of (normal, zoom) tuples
        self.image_cache = []

        grid_frame = ctk.CTkFrame(container, fg_color="transparent")
        grid_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # 👉 3 columns now
        grid_frame.grid_columnconfigure(0, weight=1, uniform="col")
        grid_frame.grid_columnconfigure(1, weight=1, uniform="col")
        grid_frame.grid_columnconfigure(2, weight=1, uniform="col")

        for idx, attraction in enumerate(self.attractions):
            row = idx // 3
            col = idx % 3
            self.create_card(grid_frame, attraction, row, col)

    # ---------- helper: safe image loader ----------
    @staticmethod
    def _safe_ctk_image(path, size):
        """
        Try to open path with PIL and produce a ctk.CTkImage sized to `size`.
        Returns None on failure.
        """
        if not path:
            return None
        try:
            # normalize path (helps with inconsistent separators)
            path = os.path.normpath(path)
            if not os.path.isabs(path):
                # keep relative paths relative to current working dir
                path = os.path.join(os.getcwd(), path) if not os.path.exists(path) else path

            if not os.path.exists(path):
                # still doesn't exist
                raise FileNotFoundError(f"Image not found: {path}")

            pil_img = Image.open(path).convert("RGBA")
            return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        except Exception as e:
            # don't crash; just return None
            print(f"[TopAttractionsPage] Warning: couldn't load image '{path}': {e}")
            return None

    def create_card(self, parent, attraction, row, col):
        # Larger visual sizes (bigger image)
        CARD_W, CARD_H = 360, 260
        IMG_W, IMG_H = 360, 240
        ZOOM_W, ZOOM_H = 390, 240

        # Underlay shadow for depth
        shadow = ctk.CTkFrame(parent, width=CARD_W+8, height=CARD_H+8, corner_radius=22, fg_color="#E6EEF8")
        shadow.grid(row=row, column=col, padx=10, pady=10, sticky="n")
        shadow.grid_propagate(False)

        card = ctk.CTkFrame(parent, width=CARD_W, height=CARD_H, corner_radius=18, fg_color="#FFFFFF")
        card.grid(row=row, column=col, padx=6, pady=4, sticky="n")
        card.grid_propagate(False)

        # Top-right bookmark heart
        #heart_lbl = ctk.CTkLabel(card, text="♡", font=ctk.CTkFont(size=14, weight="bold"))
        #heart_lbl.place(relx=0.94, rely=0.06, anchor="ne")

        # Image frame (to hold image + overlay)
        img_frame = ctk.CTkFrame(card, fg_color="transparent", width=IMG_W, height=IMG_H)
        img_frame.place(x=0, y=0)
        img_frame.grid_propagate(False)

        img_label = ctk.CTkLabel(img_frame, text="")
        img_label.place(relx=0.5, rely=0.5, anchor="center")
        img_label._current_img = None

        # load images using your safe helper
        normal = self._safe_ctk_image(attraction.get("image", "") or None, (IMG_W, IMG_H))
        zoom = self._safe_ctk_image(attraction.get("image", "") or None, (ZOOM_W, ZOOM_H))

        if normal:
            self.image_cache.append((normal, zoom))
            img_label.configure(image=normal)
            img_label._current_img = normal
        else:
            placeholder = ctk.CTkFrame(img_frame, corner_radius=12, fg_color="#F1F5F9", width=IMG_W-20, height=IMG_H-20)
            placeholder.place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(placeholder, text="No image", font=ctk.CTkFont(size=12)).place(relx=0.5, rely=0.5, anchor="center")
            img_label._current_img = None

        # Gradient-like overlay area at bottom to ensure text readability
        overlay_height = int(IMG_H * 0.30)
        overlay = ctk.CTkFrame(img_frame, fg_color="transparent", width=IMG_W, height=overlay_height)
        overlay.place(relx=0, rely=1.0, anchor="sw")

        # Title (on overlay) - only name + short text (no stars)
        name_text = attraction.get("name", "Unknown")
        title_lbl = ctk.CTkLabel(overlay, text=name_text, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        title_lbl.place(relx=0.03, rely=0.25, anchor="w")

        desc_text = attraction.get("desc", "") or attraction.get("summary", "")
        desc_lbl = ctk.CTkLabel(overlay, text=(desc_text[:120] + ("…" if len(desc_text) > 120 else "")),
                                font=ctk.CTkFont(size=11), anchor="w", wraplength=IMG_W-24)
        desc_lbl.place(relx=0.03, rely=0.65, anchor="w")

        # keep space below overlay for visual separation
        # Back area is already handled in detail; we keep card minimal here.

        # Hover behavior: swap to zoom image and show border
        def on_enter(event=None):
            if zoom is not None and getattr(img_label, "_current_img", None) is not zoom:
                img_label.configure(image=zoom)
                img_label._current_img = zoom
            card.configure(border_width=2, border_color="#0078D4")
            try:
                card.configure(cursor="hand2")
            except Exception:
                pass

        def on_leave(event=None):
            if normal is not None and getattr(img_label, "_current_img", None) is not normal:
                img_label.configure(image=normal)
                img_label._current_img = normal
            card.configure(border_width=0)
            try:
                card.configure(cursor="")
            except Exception:
                pass

        def on_click(event=None):
            app = self.winfo_toplevel()
            if hasattr(app, "show_attraction_page"):
                app.show_attraction_page(attraction)
            else:
                print("[TopAttractionsPage] show_attraction_page not found on app")


        interactive_widgets = (card, img_frame, img_label, title_lbl, desc_lbl)
        for w in interactive_widgets:
            w.bind("<Enter>", on_enter, add="+")
            w.bind("<Leave>", on_leave, add="+")
            w.bind("<Button-1>", on_click, add="+")


class AttractionDetailPage(ctk.CTkFrame):
    def __init__(self, parent, attraction, go_back_callback):
        super().__init__(parent)

        self.attraction = attraction
        self.go_back = go_back_callback

        # Title
        ctk.CTkLabel(
            self,
            text=attraction.get("name", "Details"),
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=10)

        location = attraction.get("location", "Location not specified")
        ctk.CTkLabel(
            self,
            text=f"📍 {location}",
            font=ctk.CTkFont(size=16)
        ).pack(pady=(0, 10))

        # Load markdown or content
        content = self.get_content()

        # Text viewer
        text_frame = ctk.CTkFrame(self)
        text_frame.pack(fill="both", expand=True, padx=15, pady=10)

        text_box = ctk.CTkTextbox(text_frame, wrap="word")
        text_box.pack(fill="both", expand=True)
        text_box.insert("1.0", content)
        text_box.configure(state="disabled")

        # Back button
        ctk.CTkButton(
            self,
            text="← Back to Top Attractions",
            command=self.go_back,
            fg_color="gray25",
        ).pack(pady=12)

    def get_content(self) -> str:
        # Try content_file first
        path = self.attraction.get("content_file")
        if path:
            return load_content_from_file(path)

        # Then content text
        content = self.attraction.get("content")
        if content:
            # If it looks like a file path, treat it as file
            if content.endswith((".md", ".txt")) and ("/" in content or "\\" in content):
                return load_content_from_file(content)
            return content

        # Last fallback
        return self.attraction.get("summary") or "No description available."


class AttractionDetailPageBrochure(ctk.CTkFrame):
    def __init__(self, parent, attraction, go_back_callback):
        super().__init__(parent)
        self.attraction = attraction
        self.go_back = go_back_callback

        # ===== Hero section (image + title) =====
        hero = ctk.CTkFrame(self, fg_color="#0F172A")
        hero.pack(fill="x", padx=0, pady=0)

        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=1)

        # Left: image (if available)
        img_frame = ctk.CTkFrame(hero, fg_color="transparent")
        img_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=16)

        img_label = ctk.CTkLabel(img_frame, text="")
        img_label.pack(fill="both", expand=True)

        try:
            img = Image.open(attraction.get("image", ""))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(400, 220))
            img_label.configure(image=ctk_img)
            self._hero_image = ctk_img  # keep ref so it doesn't get GC'd
        except Exception:
            img_label.configure(text="No image", text_color="white")

        # Right: title + location + back button
        info_frame = ctk.CTkFrame(hero, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=16)
        info_frame.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            info_frame,
            text=attraction.get("name", "Details"),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white",
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            info_frame,
            text=f"📍 {attraction.get('location', 'Location not specified')}",
            font=ctk.CTkFont(size=14),
            text_color="#E5E7EB",
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            info_frame,
            text="Browse detailed info, travel tips, and nearby highlights.",
            font=ctk.CTkFont(size=12),
            text_color="#CBD5F5",
            wraplength=360,
        ).pack(anchor="w", pady=(0, 14))

        ctk.CTkButton(
            info_frame,
            text="← Back to Top Attractions",
            width=200,
            height=32,
            fg_color="#1D4ED8",
            hover_color="#1E40AF",
            text_color="white",
            command=self.go_back,
        ).pack(anchor="w")

        # ===== Main area: 2 columns =====
        main = ctk.CTkFrame(self, fg_color="#F3F6FB")
        main.pack(fill="both", expand=True, padx=0, pady=(0, 0))

        # Left = blog content, Right = info cards
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # ----- LEFT: scrollable article -----
        left_scroll = ctk.CTkScrollableFrame(main, fg_color="white", corner_radius=0)
        # More padding on left so text isn't glued to the edge
        left_scroll.grid(row=0, column=0, sticky="nsew", padx=(40, 20), pady=20)
        left_scroll.grid_columnconfigure(0, weight=1)

        # Inner wrapper to add internal padding for the text
        content_wrapper = ctk.CTkFrame(left_scroll, fg_color="transparent")
        content_wrapper.pack(fill="both", expand=True, padx=25, pady=10)
        content_wrapper.grid_columnconfigure(0, weight=1)

        content = self.get_content()
        self.render_bangla_article(content_wrapper, content)

        # ----- RIGHT: trip info cards -----
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)

        self.build_info_cards(right)

    # ---------- content loading ----------
    def get_content(self):
        path = self.attraction.get("content_file")
        if path:
            return load_content_from_file(path)

        content = self.attraction.get("content")
        if content:
            if content.endswith((".md", ".txt")) and ("/" in content or "\\" in content):
                return load_content_from_file(content)
            return content

        return self.attraction.get("summary") or "No description available."

    # ---------- Bangla article renderer with arrow headings ----------
    def render_bangla_article(self, parent, text: str):
        """
        Understands your current format, e.g.:

            <-কক্সবাজার সমুদ্র সৈকত->
            normal paragraph...

            <-কক্সবাজার ভ্রমণের উপযুক্ত সময়->

        First arrow heading = big centered title.
        Others = section titles.
        Lines starting with '*' = bullets.
        """

        # 🔤 CHANGE FONT HERE IF YOU WANT
        # Use a Bangla-capable font installed on your system, or keep None.
        # Examples: "Nirmala UI", "Vrinda", "Siyam Rupali", "SolaimanLipi"
        BENGALI_FONT = None

        body_font   = ctk.CTkFont(family=BENGALI_FONT, size=15)
        h1_font     = ctk.CTkFont(family=BENGALI_FONT, size=22, weight="bold")
        h2_font     = ctk.CTkFont(family=BENGALI_FONT, size=18, weight="bold")
        bullet_font = ctk.CTkFont(family=BENGALI_FONT, size=15)

        lines = text.splitlines()
        row = 0
        buffer = []
        first_arrow_heading_seen = False

        def flush_paragraph():
            nonlocal row, buffer
            if not buffer:
                return
            paragraph = " ".join(buffer).strip()
            if paragraph:
                lbl = ctk.CTkLabel(
                    parent,
                    text=paragraph,
                    font=body_font,
                    text_color="#111827",
                    justify="left",
                    wraplength=520,   # safe width so it doesn't get cut
                )
                lbl.grid(row=row, column=0, sticky="w", padx=(10, 0), pady=(2, 10))
                row += 1
            buffer = []

        for line in lines:
            stripped = line.strip()

            # empty line => paragraph break
            if not stripped:
                flush_paragraph()
                continue

            # ----- arrow headings: <- heading ->
            if stripped.startswith("<-") and stripped.endswith("->"):
                flush_paragraph()
                heading_text = stripped[2:-2].strip()

                if not first_arrow_heading_seen:
                    first_arrow_heading_seen = True
                    # main big centered title
                    lbl = ctk.CTkLabel(
                        parent,
                        text=heading_text,
                        font=h1_font,
                        text_color="#111827",
                        justify="center",
                        wraplength=520,
                    )
                    lbl.grid(row=row, column=0, sticky="ew", padx=(10, 10), pady=(12, 8))
                else:
                    # section heading
                    lbl = ctk.CTkLabel(
                        parent,
                        text=heading_text,
                        font=h2_font,
                        text_color="#111827",
                        justify="left",
                        wraplength=520,
                    )
                    lbl.grid(row=row, column=0, sticky="w", padx=(10, 0), pady=(16, 6))

                row += 1
                continue

            # ----- bullets: starting with '*'
            if stripped.startswith("*"):
                flush_paragraph()
                bullet_text = stripped.lstrip("*").strip()
                bullet_row = ctk.CTkFrame(parent, fg_color="transparent")
                bullet_row.grid(row=row, column=0, sticky="w", padx=(10, 0), pady=2)

                ctk.CTkLabel(
                    bullet_row,
                    text="•",
                    font=bullet_font,
                    text_color="#111827",
                    width=14,
                ).pack(side="left")

                ctk.CTkLabel(
                    bullet_row,
                    text=bullet_text,
                    font=bullet_font,
                    text_color="#111827",
                    justify="left",
                    wraplength=500,
                ).pack(side="left")

                row += 1
                continue

            # normal text → part of a paragraph
            buffer.append(stripped)

        flush_paragraph()

 
    # ---------- info cards on the right ----------
    def build_info_cards(self, parent):
        best_time = self.attraction.get("best_time", "November–March (dry & pleasant)")
        duration = self.attraction.get("ideal_duration", "2–3 days")
        ideal_for = self.attraction.get("ideal_for", "Families, couples, photographers")
        highlights = self.attraction.get(
            "highlights",
            "- Sunrise or sunset views\n- Local food & markets\n- Unique cultural spots"
        )

        # Trip Snapshot
        card1 = ctk.CTkFrame(parent, corner_radius=16, fg_color="#FFFFFF")
        card1.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            card1,
            text="Trip Snapshot",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#111827",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            card1,
            text=f"🕒 Ideal duration: {duration}\n"
                 f"🎯 Ideal for: {ideal_for}",
            font=ctk.CTkFont(size=12),
            text_color="#374151",
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Best time
        card2 = ctk.CTkFrame(parent, corner_radius=16, fg_color="#DBEAFE")
        card2.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            card2,
            text="Best time to visit",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#1E3A8A",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            card2,
            text=best_time,
            font=ctk.CTkFont(size=12),
            text_color="#1E3A8A",
            justify="left",
            wraplength=260,
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Highlights
        card3 = ctk.CTkFrame(parent, corner_radius=16, fg_color="#FEF3C7")
        card3.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            card3,
            text="Highlights",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#92400E",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            card3,
            text=highlights,
            font=ctk.CTkFont(size=12),
            text_color="#92400E",
            justify="left",
            wraplength=260,
        ).pack(anchor="w", padx=12, pady=(0, 10))




class ItinerariesPage(ctk.CTkFrame):
    """
    Clean ItinerariesPage with:
      - left: Trip Details (scrollable card)
      - right: Cost Summary (compact)
      - bottom: results (compact day-cards)
      - custom scrollable dropdowns for districts (fixed height)
    """

    # full district list (module-level would be fine too; kept here for easy paste)
    DISTRICTS = [
        "Bagerhat","Bandarban","Barguna","Barisal","Bhola","Bogra","Brahmanbaria","Chandpur",
        "Chapai Nawabganj","Chattogram","Chuadanga","Cox's Bazar","Cumilla","Dhaka","Dinajpur",
        "Feni","Gaibandha","Gazipur","Gopalganj","Habiganj","Jamalpur","Jessore","Jhalokati",
        "Jhenaidah","Joypurhat","Khagrachhari","Khulna","Kishoreganj","Kurigram","Kushtia",
        "Lakshmipur","Lalmonirhat","Madaripur","Magura","Manikganj","Maulvibazar","Meherpur",
        "Munshiganj","Mymensingh","Naogaon","Natore","Nawabganj","Netrokona","Nilphamari",
        "Noakhali","Pabna","Panchagarh","Patuakhali","Pirojpur","Rajbari","Rajshahi","Rangamati",
        "Rangpur","Satkhira","Shariatpur","Sherpur","Sirajganj","Sunamganj","Sylhet","Tangail",
        "Thakurgaon"
    ]

    def __init__(self, parent):
        super().__init__(parent)

        # ---------- Header ----------
        header = ctk.CTkFrame(self, fg_color="#0F172A")
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="🗺 Build Your Custom Itinerary",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(pady=10)

        # ---------- Main background (grid: top split + bottom results) ----------
        main = ctk.CTkFrame(self, fg_color="#F3F6FB")
        main.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        main.grid_rowconfigure(1, weight=1)         # results row expands
        main.grid_columnconfigure(0, weight=2)      # left column (2/3)
        main.grid_columnconfigure(1, weight=1)      # right column (1/3)

        # ---------- TOP LEFT: Trip Details card (scrollable inner) ----------
        form_card = ctk.CTkFrame(main, fg_color="white", corner_radius=14)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(6, 8), pady=(0, 10))
        form_card.configure(width=760, height=300)
        form_card.pack_propagate(False)

        # scrollable inner area for the form so it never clips
        inner_scroll = ctk.CTkScrollableFrame(form_card, fg_color="transparent")
        inner_scroll.pack(fill="both", expand=True, padx=14, pady=12)
        inner = inner_scroll
        inner.grid_columnconfigure(0, weight=0, minsize=160)
        inner.grid_columnconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(inner, text="Trip Details", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#0F172A").grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # -------------------- Variables / controls --------------------
        DAYS_OPTIONS = ["1", "3", "5", "7", "10", "14"]
        PEOPLE_OPTIONS = [str(i) for i in range(1, 11)]
        # include a "No room" option for day trips
        ROOMS_OPTIONS = ["No room (day trip)", "1", "2", "3", "4", "5"]


        self.days_var = ctk.StringVar(value="3")
        self.people_var = ctk.StringVar(value="2")
        self.rooms_var = ctk.StringVar(value="1")
        self.tier_var = ctk.StringVar(value="Comfortable")
        self.transport_var = ctk.StringVar(value="Bus")
        self.origin_var = ctk.StringVar(value="Dhaka")
        self.destination_var = ctk.StringVar(value="Cox's Bazar")

        # row helper
        self._r = 1
        def add_row(text_label, widget):
            r = self._r
            lbl = ctk.CTkLabel(inner, text=text_label, anchor="w", font=ctk.CTkFont(size=12))
            lbl.grid(row=r, column=0, sticky="w", padx=(6, 10), pady=6)
            widget.grid(row=r, column=1, sticky="ew", padx=(0, 6), pady=6)
            self._r += 1

        # Add dropdowns & option menus
        add_row("Days:", ctk.CTkOptionMenu(inner, values=DAYS_OPTIONS, variable=self.days_var))
        add_row("People:", ctk.CTkOptionMenu(inner, values=PEOPLE_OPTIONS, variable=self.people_var))
        add_row("Rooms:", ctk.CTkOptionMenu(inner, values=ROOMS_OPTIONS, variable=self.rooms_var))
        add_row("Travel Style:", ctk.CTkOptionMenu(inner, values=["budget", "comfortable", "luxury"], variable=self.tier_var))
        add_row("Transport:", ctk.CTkOptionMenu(inner, values=["bus", "train", "air"], variable=self.transport_var))

        # -------------------- custom scrollable dropdowns for districts --------------------
        # helper: create a button that opens a fixed-height scrollable popup listing values
        def make_scroll_dropdown(parent, var: ctk.StringVar, values: list, width=200, popup_height=260):
            # create a button showing current selection
            btn = ctk.CTkButton(parent, text=var.get(), width=width, anchor="w")

            # keep button label in sync with var
            def _update_btn(*_):
                try:
                    btn.configure(text=var.get())
                except Exception:
                    pass
            try:
                var.trace_add("write", _update_btn)
            except Exception:
                # older tkinter fallback
                try:
                    var.trace("w", _update_btn)
                except Exception:
                    pass

            def open_popup():
                # top-level popup (use CTkToplevel if available)
                try:
                    popup = ctk.CTkToplevel(self)
                except Exception:
                    import tkinter as tk
                    popup = tk.Toplevel(self)
                popup.overrideredirect(True)
                popup.transient(self)

                # calculate popup position below the button
                bx = btn.winfo_rootx()
                by = btn.winfo_rooty() + btn.winfo_height()
                popup.geometry(f"+{bx}+{by}")

                # closing helper
                def close_popup(e=None):
                    try:
                        popup.grab_release()
                    except Exception:
                        pass
                    try:
                        popup.destroy()
                    except Exception:
                        pass

                # frame + scrollable area inside popup
                pop_frame = ctk.CTkFrame(popup, fg_color="white")
                pop_frame.pack(fill="both", expand=True)

                scroll = ctk.CTkScrollableFrame(pop_frame, fg_color="transparent", width=width, height=popup_height)
                scroll.pack(fill="both", expand=True, padx=6, pady=6)

                # create item buttons
                def on_select(val):
                    var.set(val)
                    close_popup()

                for val in values:
                    item = ctk.CTkButton(scroll, text=val, anchor="w", height=32,
                                         command=lambda v=val: on_select(v))
                    item.pack(fill="x", pady=2, padx=2)

                # focus & grab to keep popup open until user clicks outside or presses Escape
                try:
                    popup.grab_set()
                except Exception:
                    pass
                popup.focus_force()

                # close on Escape
                popup.bind("<Escape>", close_popup)

                try:
                    popup.grab_set()
                except Exception:
                    pass

                # If popup loses focus (user clicked elsewhere), close it
                popup.bind("<FocusOut>", lambda e: close_popup())
                # Also ensure closing via window manager
                try:
                    popup.protocol("WM_DELETE_WINDOW", close_popup)
                except Exception:
                    pass

            btn.configure(command=open_popup)
            return btn

        origin_dropdown = make_scroll_dropdown(inner, self.origin_var, self.DISTRICTS, width=200, popup_height=260)
        
        try:
            attractions_list = load_attractions() or []
            place_names = [a.get("name", "Unknown") for a in attractions_list]
            if not place_names:
                place_names = ["No attractions available"]
        except Exception:
            place_names = ["No attractions available"]

        # set a sensible default if one not already chosen
        if not self.destination_var.get():
            self.destination_var.set(place_names[0])

        # create popup dropdown with attraction names
        destination_dropdown = make_scroll_dropdown(inner, self.destination_var, place_names, width=260, popup_height=320)

        add_row("Starting District:", origin_dropdown)
        add_row("Destination:", destination_dropdown)

        # -------------------- Generate & Save buttons --------------------
        gen_btn = ctk.CTkButton(inner, text="Generate Itinerary", fg_color="#2563EB", hover_color="#1D4ED8",
                                height=40, command=self.on_generate)
        gen_btn.grid(row=self._r, column=0, columnspan=2, pady=(12, 6), padx=8, sticky="ew")
        self._r += 1

        self._r += 1

        # ---------- TOP RIGHT: Cost Summary ----------
        summary_card = ctk.CTkFrame(main, fg_color="#FFFFFF", corner_radius=12)
        summary_card.grid(row=0, column=1, sticky="nsew", padx=(8, 6), pady=(0, 10))
        summary_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(summary_card, text="Cost Summary", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        # styled summary labels
        self.summary_total_lbl = ctk.CTkLabel(summary_card, text="Grand total: —", font=ctk.CTkFont(size=16, weight="bold"), text_color="#0F172A")
        self.summary_total_lbl.pack(anchor="w", padx=12, pady=(6, 2))

        self.summary_sub_lbl = ctk.CTkLabel(summary_card, text="(Estimated breakdown below)", font=ctk.CTkFont(size=11), text_color="#6B7280")
        self.summary_sub_lbl.pack(anchor="w", padx=12, pady=(0, 6))

        self.summary_details_lbl = ctk.CTkLabel(summary_card, text="No plan yet", justify="left", wraplength=260, text_color="#374151", font=ctk.CTkFont(size=11))
        self.summary_details_lbl.pack(anchor="w", padx=12, pady=(0, 12), fill="both", expand=False)

        # ---------- BOTTOM: Results area (spans both columns) ----------
        results_frame = ctk.CTkFrame(main, fg_color="transparent")
        results_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=6, pady=(6, 0))
        results_frame.grid_columnconfigure(0, weight=3)
        results_frame.grid_columnconfigure(1, weight=1)

        # left: scrollable day-cards area
        left_results = ctk.CTkScrollableFrame(results_frame, fg_color="#FFFFFF", corner_radius=12)
        left_results.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=6)
        left_results.grid_columnconfigure(0, weight=1)

        self.it_scroll = left_results
        # fonts for itinerary rendering
        self._it_heading_font = ctk.CTkFont(size=13, weight="bold")
        self._it_text_font = ctk.CTkFont(size=11)

        # right: quick actions
        right_panel = ctk.CTkFrame(results_frame, fg_color="#FFFFFF", corner_radius=12)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=6)
        ctk.CTkLabel(right_panel, text="Quick Actions", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(12, 6))
        ctk.CTkButton(right_panel, text="Export PDF", width=140, command=self.export_plan_pdf).pack(anchor="w", padx=12, pady=(6,4))
        ctk.CTkButton(right_panel, text="Show on Map", width=140, command=self.on_show_map_quick).pack(anchor="w", padx=12, pady=(4,6))

        # last plan container
        self.last_plan = None

    # ----------------- generation & rendering -----------------
    def on_generate(self):
        # parse inputs and validate
        try:
            days = int(self.days_var.get())
            people = int(self.people_var.get())
            rooms = int(self.rooms_var.get())
            tier = self.tier_var.get()
            transport = self.transport_var.get()
            origin = self.origin_var.get().strip()
            destination = self.destination_var.get().strip()
        except Exception:
            self._show_message("Please enter valid values for days, people and rooms.")
            return

        if days < 1 or days > 14:
            self._show_message("Days must be between 1 and 14.")
            return
        if people < 1:
            self._show_message("People must be at least 1.")
            return

        # load attractions and try to match dest/coords
        attractions = load_attractions() or []
        dest_attractions = []
        dest_coords = None
        q = destination.strip().lower()

        # 1) try direct match by name/location/slug
        for a in attractions:
            if any(q in (str(a.get(field) or "")).lower() or (str(a.get(field) or "")).lower() in q
                for field in ("name", "location", "slug")):
                dest_attractions.append(a)
                if not dest_coords and a.get("coords"):
                    try:
                        dest_coords = tuple(a.get("coords"))
                    except Exception:
                        pass

        # 2) fallback to the CITY_COORDS resolver (covers "Sundarbans", typos etc.)
        if not dest_coords:
            try:
                dest_coords = resolve_city_coords(destination, attractions=attractions)
            except Exception:
                dest_coords = None


        # origin coords (match attractions then resolver)
        origin_coords = None
        if origin:
            for a in attractions:
                if origin.lower() in ((a.get("name") or "").lower() + " " + (a.get("location") or "").lower()):
                    if a.get("coords"):
                        origin_coords = tuple(a.get("coords"))
                        break
            if not origin_coords:
                try:
                    origin_coords = resolve_city_coords(origin, attractions=attractions)
                except Exception:
                    origin_coords = None

        # compute costs
        cost_summary = {}
        if origin_coords and dest_coords:
            try:
                cost_summary = compute_trip_estimate(
                    origin_coords=origin_coords,
                    dest_coords=dest_coords,
                    mode=transport,
                    people=people,
                    days=days,
                    accommodation_tier=tier,
                    rooms=rooms,
                    food_tier=tier
                )
            except Exception as e:
                cost_summary = {"error": f"Cost computation failed: {e}"}
        else:
            # compute accommodation + food + local transport fallback
            nights = max(0, days)  # nights may be 0 when rooms==0
            if rooms == 0:
                accom = {"per_night": 0, "nights": 0, "total": 0}
            else:
                accom = accommodation_cost(tier, nights=max(1, days), rooms=rooms, city_multiplier=1.0)

            food = food_cost(tier, people=people, days=days)
            local_transport = 200 * people * days

            # ensure identical keys used below
            subtotal = accom.get("total", 0) + food.get("total", 0) + local_transport
            contingency = round(subtotal * 0.08, 2)
            grand_total = round(subtotal + contingency, 2)
            cost_summary = {
                "note": "Transport estimate skipped (missing origin/destination coordinates).",
                "accommodation": accom,
                "food": food,
                "local_transport": local_transport,
                "subtotal": subtotal,
                "contingency": contingency,
                "grand_total": grand_total
            }

        preset = get_preset_for_destination(destination)
        if preset:
            plan = preset_to_plan(preset, days)
        else:
            plan = self._build_simple_plan(days, dest_attractions or attractions, people)


        result_obj = {
            "requested": {"days": days, "people": people, "rooms": rooms, "tier": tier,
                          "transport": transport, "origin": origin, "destination": destination},
            "costs": cost_summary,
            "plan": plan
        }
        self.last_plan = result_obj
        self._render_result(result_obj)

    def _build_simple_plan(self, days: int, candidates: list, people: int):
        # sort by rating/popularity then take up to days*3 stops
        def score(a):
            try:
                return float(a.get("rating", 0)) if a.get("rating") is not None else 0
            except Exception:
                return 0
        pool = sorted(candidates, key=score, reverse=True)
        max_stops = min(len(pool), days * 3)
        selected = pool[:max_stops]
        per_day = []
        ptr = 0
        for d in range(days):
            stops_for_day = []
            hour = 9
            for s in range(3):
                if ptr >= len(selected):
                    break
                a = selected[ptr]
                ptr += 1
                stops_for_day.append({
                    "time": f"{hour:02d}:00",
                    "name": a.get("name"),
                    "location": a.get("location"),
                    "desc": (a.get("desc") or a.get("summary") or "")[:120],
                    "entry_fee": a.get("avg_entry_fee") or a.get("avg_fee") or 0
                })
                hour += 3
            per_day.append({"day": d + 1, "stops": stops_for_day})
        return per_day

    def _render_result(self, data: dict):
        """Render plan into card-like day rows and update styled cost summary."""
        # clear old cards
        try:
            for child in list(self.it_scroll.winfo_children()):
                child.destroy()
        except Exception:
            pass

        req = data.get("requested", {})
        costs = data.get("costs", {})
        plan = data.get("plan", [])

        # header summary at top of itinerary column
        title_frame = ctk.CTkFrame(self.it_scroll, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(4, 6), padx=6)
        title_lbl = ctk.CTkLabel(title_frame,
                                 text=f"{req.get('days')}d · {req.get('people')}p · {req.get('destination')}",
                                 font=self._it_heading_font,
                                 text_color="#0F172A")
        title_lbl.pack(anchor="w")

        row_index = 1
        if not plan:
            empty_lbl = ctk.CTkLabel(self.it_scroll, text="No itinerary available.", font=self._it_text_font, text_color="#6B7280")
            empty_lbl.grid(row=row_index, column=0, sticky="w", padx=8, pady=6)
            row_index += 1
        else:
            for d in plan:
                day_card = ctk.CTkFrame(self.it_scroll, fg_color="#F8FAFF", corner_radius=10)
                day_card.grid(row=row_index, column=0, sticky="ew", padx=8, pady=(6, 4))
                day_card.grid_columnconfigure(0, weight=1)

                hdr = ctk.CTkLabel(day_card, text=f"Day {d['day']}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#0F172A")
                hdr.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

                r = 1
                for s in d.get("stops", []):
                    stop_frame = ctk.CTkFrame(day_card, fg_color="transparent")
                    stop_frame.grid(row=r, column=0, sticky="ew", padx=10, pady=2)
                    stop_frame.grid_columnconfigure(1, weight=1)

                    time_lbl = ctk.CTkLabel(stop_frame, text=s.get("time", ""), width=72, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563EB")
                    time_lbl.grid(row=0, column=0, sticky="w")

                    name_lbl = ctk.CTkLabel(stop_frame, text=s.get("name", ""), anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
                    name_lbl.grid(row=0, column=1, sticky="w", padx=(8, 0))

                    if s.get("desc"):
                        desc_lbl = ctk.CTkLabel(day_card, text=s.get("desc"), font=self._it_text_font, text_color="#475569", wraplength=620, justify="left")
                        desc_lbl.grid(row=r + 1, column=0, sticky="w", padx=(12, 10), pady=(0, 6))
                        r += 1

                    fee = s.get("entry_fee", 0)
                    if fee:
                        fee_lbl = ctk.CTkLabel(day_card, text=f"Entry: {fee} per person", font=ctk.CTkFont(size=10), text_color="#6B7280")
                        fee_lbl.grid(row=r + 1, column=0, sticky="w", padx=(12, 10), pady=(0, 6))
                        r += 1

                    r += 1

                row_index += 1

        # ---- Update cost summary panel ----
        details_lines = []
        if isinstance(costs, dict):
            if costs.get("note"):
                details_lines.append(costs["note"])
            if costs.get("transport"):
                t = costs["transport"]
                details_lines.append(f"Transport: {t.get('mode')} • {t.get('distance_km')} km")
                details_lines.append(f"Per person (one-way): {t.get('per_personeway')}")
                details_lines.append(f"Total (roundtrip): {t.get('total_roundtrip')}")
            if costs.get("accommodation"):
                a = costs["accommodation"]
                details_lines.append(f"Accommodation: {a.get('per_night')}/night · nights: {a.get('nights')}")
                details_lines.append(f"Total accom: {a.get('total')}")
            if costs.get("food"):
                f = costs["food"]
                details_lines.append(f"Food: {f.get('per_person_day')}/p/day · total: {f.get('total')}")
            if costs.get("local_transport") is not None:
                details_lines.append(f"Local transport: {costs.get('local_transport')}")
            if costs.get("subtotal") is not None:
                details_lines.append(f"Subtotal: {costs.get('subtotal')}")
            if costs.get("contingency") is not None:
                details_lines.append(f"Contingency: {costs.get('contingency')}")
            if costs.get("grand_total") is not None:
                grand = costs.get("grand_total")
                # emphasize grand total
                try:
                    self.summary_total_lbl.configure(text=f"Grand total: {grand}", text_color="#0B5FFF")
                except Exception:
                    self.summary_total_lbl.configure(text=f"Grand total: {grand}")
        else:
            details_lines.append("No cost data available.")

        self.summary_details_lbl.configure(text="\n".join(details_lines))

    # ----------------- small utilities -----------------
    def _show_message(self, text: str):
        popup = ctk.CTkLabel(self, text=text, text_color="white", fg_color="#DC2626")
        popup.place(relx=0.5, rely=0.96, anchor="s")
        self.after(3000, popup.destroy)


    def export_plan_pdf(self):
        """Export current last_plan to a readable PDF, ask user for save location."""
        if not getattr(self, "last_plan", None):
            self._show_message("Generate a plan first.")
            return

        try:
            from tkinter import filedialog as tkf
            suggested = f"{(self.last_plan.get('requested',{}).get('destination') or 'itinerary').replace(' ', '_')}.pdf"
            path = tkf.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=suggested)
            if not path:
                return

            # call helper
            export_itinerary_to_pdf(self.last_plan, path, title=f"Itinerary — {self.last_plan.get('requested',{}).get('destination','')}")
            self._show_message("PDF exported.")
        except Exception as e:
            self._show_message(f"PDF export failed: {e}")



    def on_show_map_quick(self):
        origin = self.origin_var.get().strip()
        dest = self.destination_var.get().strip()
        # try to resolve coords (reuse your resolver)
        attractions = load_attractions() or []
        o_coords = resolve_city_coords(origin, attractions=attractions)
        d_coords = resolve_city_coords(dest, attractions=attractions)
        dist = open_google_maps_directions(origin, dest, origin_coords=o_coords, dest_coords=d_coords)
        if dist is not None:
            self._show_message(f"Distance ≈ {dist} km — opening Google Maps.")
        else:
            self._show_message("Opening Google Maps (coords not available for distance calc).")




class PlaceholderPage(ctk.CTkFrame):
    def __init__(self, parent, name):
        super().__init__(parent)

        msg_box = ctk.CTkFrame(self, corner_radius=20, fg_color="#F3F6FB")
        msg_box.pack(expand=True, padx=40, pady=40)

        ctk.CTkLabel(
            msg_box,
            text=f"🚧 {name} is under development",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#1E293B"
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            msg_box,
            text="Stay tuned! This section is coming soon.",
            font=ctk.CTkFont(size=14),
            text_color="#475569"
        ).pack(pady=(0, 20))



# ---------- RUN APP ----------
if __name__ == "__main__":
    app = App()
    app.mainloop()
