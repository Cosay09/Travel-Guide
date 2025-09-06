import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image

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

        # track sidebar state
        self.sidebar_visible = False

        # ---- Topbar ----
        self.topbar = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.topbar.pack(side="top", fill="x")

        self.menu_btn = ctk.CTkButton(
            self.topbar, text="☰", width=40, command=self.toggle_sidebar
        )
        self.menu_btn.pack(side="left", padx=10, pady=8)

        self.title_lbl = ctk.CTkLabel(
            self.topbar, text="Travel Guide", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_lbl.pack(side="left", padx=6)

        # ---- Main body (below topbar) ----
        self.body = ctk.CTkFrame(self, corner_radius=0)
        self.body.pack(side="top", fill="both", expand=True)

        # sidebar frame (starts hidden, will be packed on left)
        self.sidebar = ctk.CTkFrame(self.body, width=220, corner_radius=0)

        # content area (always present)
        self.content = ctk.CTkFrame(self.body, corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

        # pages cache
        self.pages = {}
        self.show_page("Overview")

    def build_sidebar(self):
        """Builds sidebar buttons only once."""
        if hasattr(self, "sidebar_built") and self.sidebar_built:
            return
        self.sidebar_built = True

        head = ctk.CTkLabel(
            self.sidebar, text="Menu", font=ctk.CTkFont(size=16, weight="bold")
        )
        head.pack(padx=12, pady=(14, 8), anchor="w")

        for name in PAGES:
            btn = ctk.CTkButton(
                self.sidebar,
                text=name,
                anchor="w",
                command=lambda n=name: self.show_page(n),
            )
            btn.pack(fill="x", padx=12, pady=6)

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.pack_forget()
            self.sidebar_visible = False
        else:
            self.build_sidebar()
            # ✅ pack sidebar first so it appears on the LEFT
            self.sidebar.pack(side="left", fill="y")
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
        # clear current
        for widget in self.content.winfo_children():
            widget.pack_forget()
        page=self.get_page(name)
        page.pack(fill="both", expand=True)

# ---- Example pages ----
class OverviewPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        ctk.CTkLabel(
            self,
            text="Welcome to the Travel Guide!",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=30)
        ctk.CTkLabel(self, text="Click ☰ to open the menu").pack(pady=10)


class PlaceholderPage(ctk.CTkFrame):
    def __init__(self, parent, name):
        super().__init__(parent)
        ctk.CTkLabel(
            self, text=f"{name} page coming soon…", font=ctk.CTkFont(size=18)
        ).pack(pady=40)

class TopAttractionsPage(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent)
        ctk.CTkLabel(
            self,
            text="Top Attractions",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=20)

        # Sample attractions: (name, description, image_path)
        attractions = [
            ("Cox's Bazar Beach", "Longest natural sandy sea beach.", "assets/images/coxsbazar.jpg"),
            ("Sundarbans", "Largest mangrove forest in the world.", "assets/images/sundarban.jpg"),
            ("Ahsan Manzil", "Historic palace in Dhaka.", "assets/images/ahsanmanjil.jpg"),
        ]

        self.images = []  # keep references

        for name, desc, img_path in attractions:
            img = Image.open(img_path)

            frame = ctk.CTkFrame(self, corner_radius=8)
            frame.pack(fill="x", padx=20, pady=10)

            # background image label
            bg_label = ctk.CTkLabel(frame, text="")
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

            # overlay title
            title_label = ctk.CTkLabel(frame, text=name, font=ctk.CTkFont(size=18, weight="bold"))
            title_label.place(relx=0.05, rely=0.05, anchor="nw")

            # overlay description
            desc_label = ctk.CTkLabel(frame, text=desc, wraplength=500, justify="left")
            desc_label.place(relx=0.05, rely=0.25, anchor="nw")

            def resize_image(event, bg=bg_label, pil_img=img):
                new_width = event.width
                new_height = int(event.height)   # scale fully with frame
                resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=resized_img, dark_image=resized_img, size=(new_width, new_height))
                bg.configure(image=ctk_img)
                bg.image = ctk_img  # keep reference

                # also resize text wraplength with frame
                desc_label.configure(wraplength=int(new_width * 0.9))

            frame.bind("<Configure>", resize_image)


if __name__ == "__main__":
    app = App()
    app.mainloop()
