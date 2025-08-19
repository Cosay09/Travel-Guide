import customtkinter as ctk

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
        self.geometry("1100x700")

        # Theme / appearance
        ctk.set_appearance_mode("light")      # "light", "dark", or "system"
        ctk.set_default_color_theme("blue")    # "blue", "green", "dark-blue"

        # Layout: 1 column for sidebar, 1 for content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(99, weight=1)  # pushes items up

        title = ctk.CTkLabel(self.sidebar, text="Travel Guide",
                             font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(20, 10))

        self.buttons = {}
        for name in PAGES:
            btn = ctk.CTkButton(
                self.sidebar, text=name,
                command=lambda n=name: self.show_page(n),
                anchor="w"
            )
            btn.pack(fill="x", padx=12, pady=6)
            self.buttons[name] = btn

        # Content area
        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Page cache
        self.pages = {}
        self.show_page("Overview")

    def get_page(self, name):
        if name not in self.pages:
            if name == "Overview":
                self.pages[name] = OverviewPage(self.content)
            else:
                self.pages[name] = PlaceholderPage(self.content, name)
            self.pages[name].grid(row=0, column=0, sticky="nsew")
        return self.pages[name]

    def show_page(self, name):
        page = self.get_page(name)
        page.tkraise()

class OverviewPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        ctk.CTkLabel(
            self,
            text="Welcome! Pick a destination to begin.",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=30)
        ctk.CTkLabel(
            self,
            text="This is the Overview page placeholder."
        ).pack()

class PlaceholderPage(ctk.CTkFrame):
    def __init__(self, parent, name):
        super().__init__(parent)
        ctk.CTkLabel(
            self, text=f"{name} page coming soon…",
            font=ctk.CTkFont(size=18)
        ).pack(pady=30)

if __name__ == "__main__":
    app = App()
    app.mainloop()
