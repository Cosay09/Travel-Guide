import customtkinter as ctk
import json
from utils.page_header import BluePageHeader
DATA_PATH = "pages/data/transportation.json"


class TransportationPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        BluePageHeader(self, title="Transportation Options")

        # ===== Load data =====
        self.data = self.load_data()

        # ===== Route selector =====
        selector = ctk.CTkFrame(self)
        selector.pack(fill="x", padx=20, pady=(0, 10))

        self.route_var = ctk.StringVar()

        routes = sorted(self.data.keys())
        if routes:
            self.route_var.set(routes[0])

        ctk.CTkLabel(selector, text="Route:").pack(side="left", padx=(0, 8))
        ctk.CTkOptionMenu(
            selector,
            values=routes,
            variable=self.route_var,
            command=lambda _: self.render()
        ).pack(side="left")

        # ===== Scroll area =====
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.render()

    # --------------------------------------------------
    # Data
    # --------------------------------------------------
    def load_data(self):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # --------------------------------------------------
    # Render
    # --------------------------------------------------
    def render(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        route = self.route_var.get()
        if not route:
            return

        route_data = self.data.get(route, {})
        recommended = route_data.get("recommended")

        for mode, details in route_data.items():
            if mode == "recommended":
                continue

            self.mode_card(
                mode=mode,
                data=details,
                is_recommended=(mode == recommended)
            )

    # --------------------------------------------------
    # Mode card
    # --------------------------------------------------
    def mode_card(self, mode: str, data: dict, is_recommended: bool):
        card = ctk.CTkFrame(self.scroll, corner_radius=14)
        card.pack(fill="x", pady=10)

        # ===== Header strip =====
        header = ctk.CTkFrame(card, fg_color="#EEF2FF", corner_radius=10)
        header.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(
            header,
            text=mode.upper(),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1E3A8A"
        ).pack(side="left", padx=10, pady=6)

        if is_recommended:
            ctk.CTkLabel(
                header,
                text="⭐ Recommended",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#047857"
            ).pack(side="right", padx=10)

        # ===== Content =====
        for key, value in data.items():

            # ---- Best For (pill badges) ----
            if key == "best_for" and isinstance(value, list):
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(anchor="w", padx=14, pady=(2, 6))

                ctk.CTkLabel(
                    row,
                    text="Best for:",
                    font=ctk.CTkFont(size=12, weight="bold")
                ).pack(side="left", padx=(0, 6))

                for tag in value:
                    ctk.CTkLabel(
                        row,
                        text=tag,
                        font=ctk.CTkFont(size=11),
                        fg_color="#DBEAFE",
                        text_color="#1E3A8A",
                        corner_radius=12,
                        padx=8,
                        pady=2
                    ).pack(side="left", padx=4)

                continue

            # ---- Dictionaries (e.g. terminals) ----
            if isinstance(value, dict):
                ctk.CTkLabel(
                    card,
                    text=f"{key.replace('_', ' ').title()}:",
                    font=ctk.CTkFont(size=12, weight="bold")
                ).pack(anchor="w", padx=14, pady=(6, 2))

                for sub_k, sub_v in value.items():
                    ctk.CTkLabel(
                        card,
                        text=f"• {sub_k.title()}: {', '.join(sub_v)}",
                        font=ctk.CTkFont(size=12),
                        text_color="#374151"
                    ).pack(anchor="w", padx=28, pady=1)
                continue

            # ---- Lists ----
            if isinstance(value, list):
                text = ", ".join(value)
            else:
                text = value

            # ---- Notes / alerts coloring ----
            text_color = "#374151"
            if key in ["notes", "alerts"]:
                text_color = "#92400E"

            ctk.CTkLabel(
                card,
                text=f"{key.replace('_', ' ').title()}: {text}",
                wraplength=720,
                justify="left",
                text_color=text_color
            ).pack(anchor="w", padx=14, pady=2)

        # ----- spacing -----
        ctk.CTkFrame(card, height=8, fg_color="transparent").pack()
