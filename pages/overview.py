import customtkinter as ctk

class OverviewPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        # ===== HERO BANNER =====
        hero = ctk.CTkFrame(self, corner_radius=0, fg_color="#0078D4")
        hero.pack(fill="x", padx=0, pady=0)

        title = ctk.CTkLabel(
            hero,
            text="Discover Bangladesh",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="white",
        )
        title.pack(pady=(18, 4))

        subtitle = ctk.CTkLabel(
            hero,
            text="Curated destinations, itineraries, and travel insights across Bangladesh.",
            font=ctk.CTkFont(size=14),
            text_color="#E5E7EB",
            wraplength=900,
        )
        subtitle.pack(pady=(0, 14))

        # ===== MAIN CONTENT AREA =====
        main = ctk.CTkFrame(self, fg_color="#F3F6FB")  # soft background
        main.pack(fill="both", expand=True, padx=0, pady=0)

        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=2)
        main.grid_columnconfigure(1, weight=1)

        # ---------- LEFT: Quick actions & steps ----------
        left = ctk.CTkFrame(main, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=(15, 20))

        ctk.CTkLabel(
            left,
            text="Start exploring in a few taps",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#0F172A",
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            left,
            text="Jump into the most useful sections of the guide.",
            font=ctk.CTkFont(size=13),
            text_color="#334155",
        ).pack(anchor="w", pady=(0, 12))

        # Quick action buttons
        actions = ctk.CTkFrame(left, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 12))

        def go(page_name: str):
            app = self.winfo_toplevel()
            app.show_page(page_name)

        ctk.CTkButton(
            actions,
            text="Explore Top Attractions",
            height=40,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="white",
            command=lambda: go("Top Attractions"),
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            actions,
            text="Plan your Itineraries",
            height=40,
            fg_color="#16A34A",
            hover_color="#15803D",
            text_color="white",
            command=lambda: go("Itineraries"),
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            actions,
            text="Travel Information",
            height=40,
            fg_color="#F97316",
            hover_color="#EA580C",
            text_color="white",
            command=lambda: go("Practical Info"),
        ).pack(fill="x", pady=4)

        # 4 colorful step cards
        steps_frame = ctk.CTkFrame(left, fg_color="transparent")
        steps_frame.pack(fill="both", expand=True, pady=(10, 0))

        steps_frame.grid_columnconfigure(0, weight=1)
        steps_frame.grid_columnconfigure(1, weight=1)

        self._create_step_card(
            steps_frame,
            row=0, col=0,
            emoji="📍",
            title="Choose a destination",
            text="Browse beaches, hills, forests and cities with photos and key highlights.",
            bg="#DBEAFE",
            target_page="Top Attractions"
        )
        self._create_step_card(
            steps_frame,
            row=0, col=1,
            emoji="🗓",
            title="Shape your days",
            text="Use suggested 1–3 day plans or combine spots into your own trip.",
            bg="#DCFCE7",
            target_page="Itineraries"
        )
        self._create_step_card(
            steps_frame,
            row=1, col=0,
            emoji="🚆",
            title="Travel logistics",
            text="Check transport options, timings and tips so you reach easily.",
            bg="#FEF3C7",
        )
        self._create_step_card(
            steps_frame,
            row=1, col=1,
            emoji="🍛",
            title="Find Hidden gems",
            text="Find must-places to vist and local experiences near each place.",
            bg="#FFE4E6",
            target_page="Nearby trips & hidden gems"
        )

        # ---------- RIGHT: Highlight / inspiration ----------
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=(15, 20))

        highlight = ctk.CTkFrame(right, corner_radius=18, fg_color="#0F172A")
        highlight.pack(fill="both", expand=False, pady=(0, 12))

        ctk.CTkLabel(
            highlight,
            text="Suggested Destinations",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white",
        ).pack(anchor="w", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            highlight,
            text=(
                "Popular starting points:\n\n"
                "• Cox’s Bazar – Beaches & coastal drives\n"
                "• Sajek Valley – Hills and viewpoints\n"
                "• Sundarbans – Wildlife and waterways\n\n"
                "Browse Top Attractions for more."
            ),
            justify="left",
            font=ctk.CTkFont(size=13),
            text_color="#E5E7EB",
        ).pack(anchor="w", padx=14, pady=(0, 12))

        ctk.CTkButton(
            highlight,
            text="View Top Attractions →",
            height=34,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="white",
            command=lambda: go("Top Attractions"),
        ).pack(anchor="w", padx=14, pady=(0, 14))

        # Small info card at bottom right
        tip = ctk.CTkFrame(right, corner_radius=14, fg_color="#E0F2FE")
        tip.pack(fill="x")

        ctk.CTkLabel(
            tip,
            text="Tip",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#0F172A",
        ).pack(anchor="w", padx=10, pady=(8, 0))

        ctk.CTkLabel(
            tip,
            text="You can always return here from the menu\nif you feel lost while exploring.",
            font=ctk.CTkFont(size=12),
            text_color="#1F2933",
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 8))

    def _create_step_card(self, parent, row, col, emoji, title, text, bg, target_page=None):
        """Small colorful card for the 4 steps (optionally clickable)."""

        card = ctk.CTkFrame(parent, corner_radius=14, fg_color="#FFFFFF", border_width=1, border_color="#E5E7EB")
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        parent.grid_rowconfigure(row, weight=1)

        # If card should navigate
        if target_page:
            card.configure(cursor="hand2")

            def on_click(event=None):
                app = self.winfo_toplevel()
                app.show_page(target_page)

            card.bind("<Button-1>", on_click)

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#0F172A",
        )
        title_label.pack(anchor="w", padx=10, pady=(8, 4))

        text_label = ctk.CTkLabel(
            card,
            text=text,
            font=ctk.CTkFont(size=12),
            justify="left",
            wraplength=260,
            text_color="#374151",
        )
        text_label.pack(anchor="w", padx=10, pady=(0, 10))

        # Make labels clickable too
        if target_page:
            title_label.configure(cursor="hand2")
            text_label.configure(cursor="hand2")
            title_label.bind("<Button-1>", on_click)
            text_label.bind("<Button-1>", on_click)
