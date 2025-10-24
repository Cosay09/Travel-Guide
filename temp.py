import customtkinter as ctk
import sqlite3
import hashlib
import os
from PIL import Image

DB_PATH = "data/users.db"

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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


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

        ctk.set_appearance_mode("dark")
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

        # Topbar
        self.topbar = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.topbar.pack(side="top", fill="x")

        self.menu_btn = ctk.CTkButton(self.topbar, text="☰", width=40, command=self.toggle_sidebar)
        self.menu_btn.pack(side="left", padx=10, pady=8)

        self.title_lbl = ctk.CTkLabel(
            self.topbar, text=f"Travel Guide ({'Guest' if self.is_guest else self.user_email})",
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
        # don't grid() it yet — keep hidden until toggled
        # self.sidebar.grid(row=0, column=0, sticky="ns")  # NOT here

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
            # use lambda bound to 'self' properly
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
            self.pages[name].pack(fill="both", expand=True)
        return self.pages[name]

    def show_page(self, name):
        # Clear old widgets from the content frame
        for widget in self.content.winfo_children():
            widget.grid_forget()

        page = self.get_page(name)
        page.grid(row=0, column=0, sticky="nsew")

        # Make sure the page expands with the content area
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
                # destroy any created page frames
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
        ctk.CTkLabel(self, text="Welcome to Travel Guide", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(60, 20))
        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email")
        self.email_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)
        ctk.CTkButton(self, text="Login", command=self.login).pack(pady=10)
        ctk.CTkButton(self, text="Register", command=self.open_register).pack(pady=5)
        ctk.CTkButton(self, text="Continue as Guest", fg_color="gray", command=self.login_guest).pack(pady=20)
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


class RegisterFrame(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.on_login_success = on_login_success
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Register New Account", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(60, 20))
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
            cur.execute("INSERT INTO users VALUES (?, ?, ?)", (email, name, hash_password(password)))
            conn.commit()
            self.message.configure(text="Registration successful!", text_color="green")
        except sqlite3.IntegrityError:
            self.message.configure(text="Email already registered")
        conn.close()

    def back_to_login(self):
        self.destroy()
        LoginFrame(self.master, self.on_login_success).pack(fill="both", expand=True)


# ---------- PAGES ----------
class OverviewPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        ctk.CTkLabel(self, text="Welcome to the Travel Guide!", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=30)
        ctk.CTkLabel(self, text="Click ☰ to open the menu").pack(pady=10)

class PlaceholderPage(ctk.CTkFrame):
    def __init__(self, parent, name):
        super().__init__(parent)
        ctk.CTkLabel(self, text=f"{name} page coming soon…", font=ctk.CTkFont(size=18)).pack(pady=40)


class TopAttractionsPage(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent)
        ctk.CTkLabel(
            self,
            text="Top Attractions",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=20)

        # Sample attractions: (name, image_path)
        attractions = [
            ("Cox's Bazar Beach", "assets/images/coxsbazar.jpg"),
            ("Saint Martin's Island", "assets/images/saint_martin.jpg"),
            ("Sundarbans", "assets/images/sundarban.jpg"),
            ("Sajek Valley", "assets/images/sajek_valley.jpg"),
            ("Ahsan Manzil", "assets/images/ahsanmanjil.jpg"),
            ("Sukhiya Valley", "assets/images/sukhiya_valley.jpg"),
            ("Kaptai Lake", "assets/images/kaptai_lake.jpg"),
            ("Jaflong", "assets/images/jaflong.jpg"),
            ("Langlok Waterfall", "assets/images/langlok_waterfall.jpg"),
            ("Bholaganj", "assets/images/bholaganj.jpg"),
            ("Tanguar Haor", "assets/images/tanguar_haor.jpg"),
            ("As-Salam Jame Mosque", "assets/images/as_salam_jame_mosque.jpg"),
        ]

        self.images = []  # keep references to CTkImages

        # create a frame to hold grid
        grid_frame = ctk.CTkFrame(self)
        grid_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # configure grid columns
        grid_frame.grid_columnconfigure(0, weight=1, uniform="col")
        grid_frame.grid_columnconfigure(1, weight=1, uniform="col")

        for idx, (name, img_path) in enumerate(attractions):
            img = Image.open(img_path)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(400, 200))
            self.images.append(ctk_img)

            # create block frame
            block = ctk.CTkFrame(grid_frame, corner_radius=20)
            block.grid(row=idx//2, column=idx%2, padx=10, pady=10, sticky="nsew")

            # image label
            img_label = ctk.CTkLabel(block, image=ctk_img, text="")
            img_label.pack(fill="both", expand=True)

            # overlay name
            name_label = ctk.CTkLabel(block, text=name, font=ctk.CTkFont(size=16, weight="bold"))
            name_label.place(relx=0.05, rely=0.05, anchor="nw")


# ---------- RUN APP ----------
if __name__ == "__main__":
    app = App()
    app.mainloop()
