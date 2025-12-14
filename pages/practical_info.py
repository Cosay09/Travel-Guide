import customtkinter as ctk
import json
from utils.page_header import BluePageHeader


DATA_PATH = "pages/data/practical_info.json"


SECTION_ICONS = {
    "Safety": "⚠️",
    "Emergency": "🚨",
    "Money & Payments": "💳",
    "Internet & SIM": "📶",
    "Local Etiquette": "👕",
    "Best Time to Visit": "🌦",
    "Beach Safety": "🏖️",
    "Travel Tips": "🧭",
    "Health Tips": "🩺",
    "Getting Around": "🚌",
    "Seasonal Travel": "🗓️",
    "Visitor Tips": "ℹ️"
}


class PracticalInfoPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)
        BluePageHeader(self, title="Practical Information")

        self.data = self.load_data()
        self.last_open_section = None


        # ===== Destination selector =====
        selector = ctk.CTkFrame(self)
        selector.pack(fill="x", padx=20, pady=(5, 10))

        self.place_var = ctk.StringVar(value="General")
        places = list(self.data.keys())

        ctk.CTkLabel(
            selector,
            text="View information for:",
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(0, 8))

        ctk.CTkOptionMenu(
            selector,
            values=places,
            variable=self.place_var,
            command=lambda _: self.render()
        ).pack(side="left")

        # ===== Scroll Area =====
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.render()

    # ---------- data ----------
    def load_data(self):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---------- render ----------
    def render(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        place = self.place_var.get()
        sections = self.data.get(place, {})

        if not sections:
            ctk.CTkLabel(
                self.scroll,
                text="No practical information available.",
                text_color="#6B7280"
            ).pack(pady=20)
            return

        for title, points in sections.items():
            auto_open = (
                title in ("Safety", "Emergency")
                if self.last_open_section is None
                else title == self.last_open_section
            )
            self.collapsible_section(title, points, auto_open)

    # ---------- UI blocks ----------
    def collapsible_section(self, title: str, points: list, auto_open=False):
        container = ctk.CTkFrame(self.scroll, corner_radius=14)
        container.pack(fill="x", pady=8)

        body = ctk.CTkFrame(container, fg_color="transparent")

        def toggle():
            if body.winfo_ismapped():
                body.pack_forget()
            else:
                body.pack(fill="x", padx=8, pady=(0, 10))
                self.last_open_section = title

        header = ctk.CTkButton(
            container,
            text=f"{SECTION_ICONS.get(title, 'ℹ️')}  {title}",
            anchor="w",
            height=40,
            fg_color="#E5E7EB",
            hover_color="#D1D5DB",
            text_color="#111827",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=toggle
        )
        header.pack(fill="x", padx=8, pady=8)

        for p in points:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(anchor="w", padx=16, pady=2)

            ctk.CTkLabel(row, text="•").pack(side="left")
            ctk.CTkLabel(
                row,
                text=p,
                wraplength=600,
                justify="left"
            ).pack(side="left")

        # ✅ Auto-open logic
        if auto_open:
            body.pack(fill="x", padx=8, pady=(0, 10))
