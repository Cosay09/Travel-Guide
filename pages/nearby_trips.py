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
        filter_bar.pack(fill="x", padx=20)

        self.base_city = ctk.StringVar(value="All")

        cities = sorted({t["from"] for t in self.trips})
        cities.insert(0, "All")

        ctk.CTkLabel(filter_bar, text="Starting from:").pack(side="left", padx=(0, 8))
        ctk.CTkOptionMenu(
            filter_bar,
            values=cities,
            variable=self.base_city,
            command=lambda _: self.render()
        ).pack(side="left")

        # ===== Scroll Area =====
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

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

        filtered = [
            t for t in self.trips
            if city == "All" or t["from"] == city
        ]

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

        title = f"{trip['name']} · {trip['distance_km']} km"
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(10, 2))

        meta = f"{trip['category']} · Ideal: {trip['ideal_duration']}"
        ctk.CTkLabel(
            card,
            text=meta,
            font=ctk.CTkFont(size=12),
            text_color="#475569"
        ).pack(anchor="w", padx=12)

        ctk.CTkLabel(
            card,
            text=trip["summary"],
            wraplength=600,
            justify="left",
            text_color="#374151"
        ).pack(anchor="w", padx=12, pady=(6, 10))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(anchor="e", padx=12, pady=(0, 10))

        ctk.CTkButton(
            actions,
            text="🗺 Open in Maps",
            height=28,
            command=lambda q=trip["map_query"]: self.open_maps(q)
        ).pack(side="right")

    # ---------- helpers ----------
    def open_maps(self, query):
        url = "https://www.google.com/maps/search/" + query.replace(" ", "+")
        webbrowser.open_new(url)
