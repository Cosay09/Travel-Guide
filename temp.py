import customtkinter as ctk
import sqlite3
import hashlib
import os
import json
from PIL import Image



DB_PATH = "data/users.db"
ATTRACTIONS_PATH = "data/attractions.json"



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
        self.resizable(True, True) # Smooth resizing allowed


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

        # ❌ no spacer here anymore

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
            else:
                self.pages[name] = PlaceholderPage(self.content, name)
            self.pages[name].grid(row=0, column=0, sticky="nsew")
        return self.pages[name]

    def show_page(self, name):
        # Clear old widgets from the content frame
        for widget in self.content.winfo_children():
            widget.grid_remove()

        page = self.get_page(name)
        page.grid(row=0, column=0, sticky="nsew")

        # Make sure the page expands with the content area
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # highlight active button in sidebar (if built)
        if getattr(self, "sidebar_built", False):
            self.highlight_sidebar(name)


    def show_attraction_page(self, attraction):
        """Show full-page attraction detail inside main content area."""
        # Optional: close sidebar for better focus
        if getattr(self, "sidebar_visible", False):
            self.toggle_sidebar()

        # Hide any current pages in content
        for widget in self.content.winfo_children():
            widget.grid_remove()

        # Create a fresh detail page (not cached)
        detail_page = AttractionDetailPageBrochure(
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

        self.image_cache = []  # keep (normal_img, zoom_img) alive

        grid_frame = ctk.CTkFrame(container, fg_color="transparent")
        grid_frame.pack(padx=20, pady=20)

        # 👉 3 columns now
        grid_frame.grid_columnconfigure(0, weight=1, uniform="col")
        grid_frame.grid_columnconfigure(1, weight=1, uniform="col")
        grid_frame.grid_columnconfigure(2, weight=1, uniform="col")

        for idx, attraction in enumerate(self.attractions):
            row = idx // 3
            col = idx % 3
            self.create_card(grid_frame, attraction, row, col)

    def create_card(self, parent, attraction, row, col):
        # Smaller size so 3 fit in a 1000px window
        CARD_W, CARD_H = 300, 200
        IMG_W, IMG_H = 300, 200
        ZOOM_W, ZOOM_H = 330, 220

        # ----- Card container -----
        card = ctk.CTkFrame(
            parent,
            width=CARD_W,
            height=CARD_H,
            corner_radius=18,
            fg_color="#FFFFFF",
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        # Image label (centered)
        img_label = ctk.CTkLabel(card, text="")
        img_label.place(relx=0.5, rely=0.5, anchor="center")

        normal = zoom = None
        try:
            img = Image.open(attraction.get("image", ""))
            normal = ctk.CTkImage(light_image=img, dark_image=img, size=(IMG_W, IMG_H))
            zoom = ctk.CTkImage(light_image=img, dark_image=img, size=(ZOOM_W, ZOOM_H))
            self.image_cache.append((normal, zoom))
            img_label.configure(image=normal)
        except Exception:
            img_label.configure(text="Image Missing", text_color="red")

        # ----- Name bar at bottom-left (no rounded corners) -----
        name_text = attraction.get("name", "Unknown")

        name_label = ctk.CTkLabel(
            card,
            text=f"  {name_text}  ",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white",
            fg_color="#0F172A",    # solid dark bar
            corner_radius=0,       # 👈 no rounded corners → no white bits
        )
        name_label.place(relx=0.02, rely=0.97, anchor="sw")

        # ----- Hover effects -----
        def on_enter(event=None):
            if zoom is not None:
                img_label.configure(image=zoom)
            card.configure(border_width=2, border_color="#0078D4")
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
        best_time = self.attraction.get("best_time", "October–March (dry & pleasant)")
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
