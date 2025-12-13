import customtkinter as ctk


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
