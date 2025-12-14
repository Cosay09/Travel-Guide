import customtkinter as ctk
from utils.accommodation_logic import get_accommodation_results, estimate_accommodation_cost
import webbrowser
from utils.page_header import BluePageHeader


class AccommodationPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)
        BluePageHeader(self, title="Top Attractions")

        # ===== Main container =====
        main = ctk.CTkFrame(self, fg_color="#F3F6FB")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=3)
        main.grid_rowconfigure(0, weight=1)

        # ===== LEFT: Search panel =====
        form = ctk.CTkFrame(main, fg_color="white", corner_radius=12)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Search Hotels",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 8)
        )

        # Variables
        self.destination_var = ctk.StringVar(value="Cox's Bazar")
        self.nights_var = ctk.StringVar(value="3")
        self.rooms_var = ctk.StringVar(value="1")
        self.tier_var = ctk.StringVar(value="comfortable")
        self.min_price_var = ctk.StringVar(value="")
        self.max_price_var = ctk.StringVar(value="")

        def add_row(r, label, widget):
            ctk.CTkLabel(form, text=label).grid(
                row=r, column=0, sticky="w", padx=12, pady=6
            )
            widget.grid(row=r, column=1, sticky="ew", padx=12, pady=6)

        add_row(1, "Destination",
                ctk.CTkEntry(form, textvariable=self.destination_var))
        add_row(2, "Nights",
                ctk.CTkEntry(form, textvariable=self.nights_var))
        add_row(3, "Rooms",
                ctk.CTkEntry(form, textvariable=self.rooms_var))
        add_row(4, "Tier",
                ctk.CTkOptionMenu(
                    form,
                    values=["budget", "comfortable", "luxury"],
                    variable=self.tier_var
                ))
        add_row(5, "Min Price",
                ctk.CTkEntry(form, textvariable=self.min_price_var))
        add_row(6, "Max Price",
                ctk.CTkEntry(form, textvariable=self.max_price_var))

        ctk.CTkButton(
            form,
            text="Search Hotels",
            fg_color="#2563EB",
            command=self.on_search
        ).grid(row=7, column=0, columnspan=2, sticky="ew",
               padx=12, pady=(12, 12))

        # ===== RIGHT: Results =====
        results_card = ctk.CTkFrame(main, fg_color="transparent")
        results_card.grid_columnconfigure(0, weight=1)
        results_card.grid(row=0, column=1, sticky="nsew")
        results_card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            results_card,
            text="Available Hotels",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="ew", padx=12, pady=(0, 8))

        self.results_scroll = ctk.CTkScrollableFrame(
            results_card, fg_color="white", corner_radius=12
        )
        self.results_scroll.grid(row=1, column=0, sticky="nsew")

    # ================= SEARCH =================
    def on_search(self):
        for child in self.results_scroll.winfo_children():
            child.destroy()

        try:
            results = get_accommodation_results(
                destination=self.destination_var.get(),
                nights=int(self.nights_var.get()),
                rooms=int(self.rooms_var.get()),
                tier=self.tier_var.get(),
                min_price=int(self.min_price_var.get()) if self.min_price_var.get() else None,
                max_price=int(self.max_price_var.get()) if self.max_price_var.get() else None
            )
        except Exception:
            self.show_message("Invalid input")
            return

        if not results:
            ctk.CTkLabel(
                self.results_scroll,
                text="No hotels found.",
                text_color="#6B7280"
            ).pack(pady=20)
            return

        self.render_results(results)

    # ================= RENDER =================
    def render_results(self, hotels):
        for hotel in hotels:
            card = ctk.CTkFrame(self.results_scroll, fg_color="#F8FAFF", corner_radius=10)
            card.pack(fill="x", padx=10, pady=8)

            card.grid_columnconfigure(0, weight=3)
            card.grid_columnconfigure(1, weight=1)
            card.grid_columnconfigure(2, weight=0)

            cost = estimate_accommodation_cost(
                hotel,
                nights=int(self.nights_var.get()),
                rooms=int(self.rooms_var.get())
            )

            ctk.CTkLabel(
                card, text=hotel["name"],
                font=ctk.CTkFont(size=13, weight="bold")
            ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))

            ctk.CTkLabel(
                card, text=hotel.get("description", ""),
                wraplength=420,
                justify="left",
                text_color="#475569"
            ).grid(row=1, column=0, sticky="w", padx=10)

            ctk.CTkLabel(
                card,
                text=f"৳ {cost['per_night']} / night · Total ৳ {cost['total']}",
                font=ctk.CTkFont(size=11),
                text_color="#0F172A"
            ).grid(row=2, column=0, sticky="w", padx=10, pady=(4, 8))

            ctk.CTkButton(
                card,
                text="🌐 Visit Website",
                height=30,
                fg_color="#2563EB",
                hover_color="#1D4ED8",
                command=lambda h=hotel: self.open_website(h)
            ).grid(row=0, column=2, rowspan=3, padx=10)

            

    def open_website(self, hotel: dict):
        url = hotel.get("website")
        if not url:
            self.show_message("Website not available")
            return

        # ensure valid URL
        if not url.startswith("http"):
            url = "https://" + url

        webbrowser.open_new(url)
            



    def show_message(self, text):
        lbl = ctk.CTkLabel(self, text=text, fg_color="#111827", text_color="white")
        lbl.place(relx=0.5, rely=0.95, anchor="center")
        self.after(2500, lbl.destroy)