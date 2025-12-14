import customtkinter as ctk


class BluePageHeader(ctk.CTkFrame):
    def __init__(self, parent, title: str, show_back: bool = True):
        super().__init__(parent, fg_color="#0078D4", corner_radius=0)
        self.pack(fill="x", padx=0, pady=0)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=16, pady=14)

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=0)

        # Title (left)
        ctk.CTkLabel(
            container,
            text=title,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="white",
        ).grid(row=0, column=0, sticky="w")

        # Back button (right)
        if show_back:
            def go_back():
                app = self.winfo_toplevel()
                app.show_page("Overview")

            ctk.CTkButton(
                container,
                text="← Back",
                width=90,
                height=34,
                fg_color="#FFFFFF",
                hover_color="#E5E7EB",
                text_color="#0078D4",
                corner_radius=8,
                command=go_back,
            ).grid(row=0, column=1, sticky="e")
