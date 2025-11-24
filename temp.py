import customtkinter as ctk
import sqlite3
import hashlib
import os
import json
from PIL import Image

# ---------- PATHS ----------
DB_PATH = "data/users.db"
ATTRACTIONS_PATH = "data/attractions.json"


# ---------- DATABASE SETUP ----------
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


# ---------- ATTRACTIONS DATA ----------
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


def load_content_from_file(path: str) -> str:
    """Load long text/blog content from .md or .txt file."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"⚠ Content file not found: {path}"
    except Exception as e:
        return f"⚠ Error loading content from {path}: {e}"


# ---------- MAIN APP ----------
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
        self.geometry("1000x600")
        self.resizable(False, False)

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
        self.sidebar = ctk.CTkFrame(self.body, width=220, corner_radius=0)

        # Content (always present)
        self.content = ctk.CTkFrame(self.body, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")  # column 1 (right side)

        self.pages = {}
        self.show_page("Overview")  # show default page

    def build_sidebar(self):
        if hasattr(self, "sidebar_built") and self.sidebar_built:
            return
        self.sidebar_built = True

        ctk.CTkLabel(
            self.sidebar, text="Menu", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=12, pady=(14, 8), anchor="w")

        for name in PAGES:
            ctk.CTkButton(
                self.sidebar,
                text=name,
                anchor="w",
                command=lambda n=name, app=self: app.show_page(n)
            ).pack(fill="x", padx=12, pady=6)

        # logout button at bottom
        ctk.CTkButton(
            self.sidebar,
            text="Logout",
            fg_color="red",
            hover_color="#b30000",
            command=self.logout
        ).pack(fill="x", padx=12, pady=20, side="bottom")

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
            else:
                self.pages[name] = PlaceholderPage(self.content, name)
            self.pages[name].grid(row=0, column=0, sticky="nsew")
        return self.pages[name]

    def show_page(self, name):
        # Hide all current widgets in content frame
        for widget in self.content.winfo_children():
            widget.grid_remove()

        page = self.get_page(name)
        page.grid(row=0, column=0, sticky="nsew")

        # Make sure the page expands with the content area
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def show_attraction_page(self, attraction):
        """Show full-page attraction detail inside main content area."""
        # Optional: close sidebar for better focus
        if getattr(self, "sidebar_visible", False):
            self.toggle_sidebar()

        # Hide any current pages in content
        for widget in self.content.winfo_children():
            widget.grid_remove()

        # Create a fresh detail page (not cached)
        detail_page = AttractionDetailPage(
            self.content,
            attraction,
            go_back_callback=lambda: self.show_page("Top Attractions")
        )
        detail_page.grid(row=0, column=0, sticky="nsew")
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


# ---------- LOGIN + REGISTER ----------
class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.on_login_success = on_login_success
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(
            self,
            text="Welcome to Travel Guide",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(60, 20))

        self.email_entry = ctk.CTkEntry(
            self,
            placeholder_text="Email",
            width=300,
            font=ctk.CTkFont(size=16)
        )
        self.email_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(
            self,
            placeholder_text="Password",
            show="*",
            width=300,
            font=ctk.CTkFont(size=16)
        )
        self.password_entry.pack(pady=10)

        # Bind Enter key to trigger login
        self.email_entry.bind("<Return>", lambda event: self.login())
        self.password_entry.bind("<Return>", lambda event: self.login())

        ctk.CTkButton(self, text="Login", command=self.login).pack(pady=10)
        ctk.CTkButton(self, text="Register", command=self.open_register).pack(pady=5)
        ctk.CTkButton(
            self,
            text="Continue as Guest",
            fg_color="gray",
            command=self.login_guest
        ).pack(pady=20)

        self.message = ctk.CTkLabel(self, text="", text_color="red")
        self.message.pack()

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
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(
            self,
            text="Register New Account",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(60, 20))

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Full Name")
        self.name_entry.pack(pady=10)

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email")
        self.email_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)

        ctk.CTkButton(self, text="Create Account", command=self.register).pack(pady=10)
        ctk.CTkButton(self, text="Back to Login", command=self.back_to_login).pack(pady=5)

        self.message = ctk.CTkLabel(self, text="", text_color="red")
        self.message.pack()

    def register(self):
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not name or not email or not password:
            self.message.configure(text="All fields are required")
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users VALUES (?, ?, ?)",
                (email, name, hash_password(password))
            )
            conn.commit()
            self.message.configure(text="Registration successful!", text_color="green")
        except sqlite3.IntegrityError:
            self.message.configure(text="Email already registered")
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




class TopAttractionsPage(FastScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent, scroll_speed=4)

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

        self.image_cache = []  # keep (normal_img, zoom_img) alive

        grid_frame = ctk.CTkFrame(container, fg_color="transparent")
        grid_frame.pack(padx=20, pady=20)

        grid_frame.grid_columnconfigure(0, weight=1, uniform="col")
        grid_frame.grid_columnconfigure(1, weight=1, uniform="col")

        for idx, attraction in enumerate(self.attractions):
            row, col = divmod(idx, 2)
            self.create_card(grid_frame, attraction, row, col)

    def create_card(self, parent, attraction, row, col):
        CARD_W, CARD_H = 380, 230
        IMG_W, IMG_H = 380, 230
        ZOOM_W, ZOOM_H = 420, 260

        # ----- Card container -----
        card = ctk.CTkFrame(
            parent,
            width=CARD_W,
            height=CARD_H,
            corner_radius=18,
            fg_color="#FFFFFF",
        )
        card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
        card.grid_propagate(False)

        # Image label (centered)
        img_label = ctk.CTkLabel(card, text="")
        img_label.place(relx=0.5, rely=0.5, anchor="center")

        normal = zoom = None
        try:
            img = Image.open(attraction.get("image", ""))
            normal = ctk.CTkImage(img, size=(IMG_W, IMG_H))
            zoom = ctk.CTkImage(img, size=(ZOOM_W, ZOOM_H))
            self.image_cache.append((normal, zoom))
            img_label.configure(image=normal)
        except Exception:
            img_label.configure(text="Image Missing", text_color="red")

        # ----- Name pill at bottom-left -----
        name_text = attraction.get("name", "Unknown")

        pill = ctk.CTkFrame(
            card,
            fg_color="#0F172A",     # dark background
            corner_radius=999,      # very round pill
        )
        pill.place(relx=0.02, rely=0.97, anchor="sw")

        name_label = ctk.CTkLabel(
            pill,
            text=name_text,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="white",
            fg_color="transparent",   # no extra box, just text
        )
        name_label.pack(padx=8, pady=3)


        # ----- Hover effects -----
        def on_enter(event=None):
            if zoom is not None:
                img_label.configure(image=zoom)
            card.configure(border_width=3, border_color="#0078D4")
            card.configure(cursor="hand2")

        def on_leave(event=None):
            if normal is not None:
                img_label.configure(image=normal)
            card.configure(border_width=0)
            card.configure(cursor="")

        # ----- Click to open detail page -----
        def on_click(event=None):
            app = self.winfo_toplevel()
            app.show_attraction_page(attraction)

        for w in (card, img_label, name_label):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)




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
