import customtkinter as ctk
import json
import webbrowser
from utils.page_header import BluePageHeader


DATA_PATH = "pages/data/nearby_trips.json"


class NearbyTripsPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)
        BluePageHeader(self, title="Nearby Trips & Hidden Gems")

        self.trips = self.load_data()

        # ===== Filters =====
        filter_bar = ctk.CTkFrame(self)
        filter_bar.pack(fill="x", padx=20, pady=(5, 10))

        self.base_city = ctk.StringVar(value="All")
        self.category = ctk.StringVar(value="All")
        self.sort_by = ctk.StringVar(value="Nearest")

        cities = sorted({t["from"] for t in self.trips})
        cities.insert(0, "All")

        categories = sorted({t["category"] for t in self.trips})
        categories.insert(0, "All")

        # --- City filter
        ctk.CTkLabel(filter_bar, text="Starting from:").pack(side="left", padx=(0, 6))
        ctk.CTkOptionMenu(
            filter_bar,
            values=cities,
            variable=self.base_city,
            command=lambda _: self.render()
        ).pack(side="left", padx=(0, 14))

        # --- Category filter
        ctk.CTkLabel(filter_bar, text="Category:").pack(side="left", padx=(0, 6))
        ctk.CTkOptionMenu(
            filter_bar,
            values=categories,
            variable=self.category,
            command=lambda _: self.render()
        ).pack(side="left", padx=(0, 14))

        # --- Sort
        ctk.CTkLabel(filter_bar, text="Sort by:").pack(side="left", padx=(0, 6))
        ctk.CTkOptionMenu(
            filter_bar,
            values=["Nearest", "Farthest"],
            variable=self.sort_by,
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

        city = self.base_city.get()
        category = self.category.get()

        filtered = [
            t for t in self.trips
            if (city == "All" or t["from"] == city)
            and (category == "All" or t["category"] == category)
        ]

        filtered.sort(
            key=lambda x: x.get("distance_km", 0),
            reverse=(self.sort_by.get() == "Farthest")
        )

        if not filtered:
            ctk.CTkLabel(
                self.scroll,
                text="No trips found.",
                text_color="#6B7280"
            ).pack(pady=20)
            return

        for trip in filtered:
            self.trip_card(trip)

    # ---------- card ----------
    def trip_card(self, trip: dict):
        card = ctk.CTkFrame(self.scroll, corner_radius=12)
        card.pack(fill="x", pady=8)

        # --- Title row
        title_row = ctk.CTkFrame(card, fg_color="transparent")
        title_row.pack(fill="x", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            title_row,
            text=f"{trip['name']} · {trip['distance_km']} km",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left")

        self.category_badge(title_row, trip["category"]).pack(side="right")

        # --- Meta
        ctk.CTkLabel(
            card,
            text=f"Ideal duration: {trip['ideal_duration']}",
            font=ctk.CTkFont(size=12),
            text_color="#475569"
        ).pack(anchor="w", padx=12)

        # --- Summary
        ctk.CTkLabel(
            card,
            text=trip["summary"],
            wraplength=600,
            justify="left",
            text_color="#374151"
        ).pack(anchor="w", padx=12, pady=(6, 10))

        # --- Actions
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(anchor="e", padx=12, pady=(0, 10))

        ctk.CTkButton(
            actions,
            text="🗺 Open in Maps",
            height=28,
            command=lambda q=trip["map_query"]: self.open_maps(q)
        ).pack(side="right")

    # ---------- helpers ----------
    def category_badge(self, parent, category: str):
        colors = {
            "Hidden Gem": "#16A34A",
            "Nearby Trip": "#2563EB",
            "Hidden Experience": "#7C3AED",
            "Nearby Experience": "#0EA5E9"
        }

        return ctk.CTkLabel(
            parent,
            text=category,
            fg_color=colors.get(category, "#6B7280"),
            text_color="white",
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            padx=8,
            pady=2
        )

    def open_maps(self, query):
        url = "https://www.google.com/maps/search/" + query.replace(" ", "+")
        webbrowser.open_new(url)
