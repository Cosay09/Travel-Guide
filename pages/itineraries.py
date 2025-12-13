import customtkinter as ctk

from pages.top_attraction.data import load_attractions
from utils.itinerary_utils import resolve_city_coords, compute_trip_estimate, accommodation_cost, food_cost
from utils.itinerary_presets import get_preset_for_destination, preset_to_plan
from utils.pdf_export import export_itinerary_to_pdf   
from utils.geo_utils import open_google_maps_directions              

class ItinerariesPage(ctk.CTkFrame):

    DISTRICTS = [
        "Bagerhat","Bandarban","Barguna","Barisal","Bhola","Bogra","Brahmanbaria","Chandpur",
        "Chapai Nawabganj","Chattogram","Chuadanga","Cox's Bazar","Cumilla","Dhaka","Dinajpur",
        "Feni","Gaibandha","Gazipur","Gopalganj","Habiganj","Jamalpur","Jessore","Jhalokati",
        "Jhenaidah","Joypurhat","Khagrachhari","Khulna","Kishoreganj","Kurigram","Kushtia",
        "Lakshmipur","Lalmonirhat","Madaripur","Magura","Manikganj","Maulvibazar","Meherpur",
        "Munshiganj","Mymensingh","Naogaon","Natore","Nawabganj","Netrokona","Nilphamari",
        "Noakhali","Pabna","Panchagarh","Patuakhali","Pirojpur","Rajbari","Rajshahi","Rangamati",
        "Rangpur","Satkhira","Shariatpur","Sherpur","Sirajganj","Sunamganj","Sylhet","Tangail",
        "Thakurgaon"
    ]

    def __init__(self, parent):
        super().__init__(parent)

        # ---------- Header ----------
        header = ctk.CTkFrame(self, fg_color="#0F172A")
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="🗺 Build Your Custom Itinerary",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(pady=10)

        # ---------- Main background (grid: top split + bottom results) ----------
        main = ctk.CTkFrame(self, fg_color="#F3F6FB")
        main.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        main.grid_rowconfigure(1, weight=1)         # results row expands
        main.grid_columnconfigure(0, weight=2)      # left column (2/3)
        main.grid_columnconfigure(1, weight=1)      # right column (1/3)

        # ---------- TOP LEFT: Trip Details card (scrollable inner) ----------
        form_card = ctk.CTkFrame(main, fg_color="white", corner_radius=14)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(6, 8), pady=(0, 10))
        form_card.configure(width=760, height=300)
        form_card.pack_propagate(False)

        # scrollable inner area for the form so it never clips
        inner_scroll = ctk.CTkScrollableFrame(form_card, fg_color="transparent")
        inner_scroll.pack(fill="both", expand=True, padx=14, pady=12)
        inner = inner_scroll
        inner.grid_columnconfigure(0, weight=0, minsize=160)
        inner.grid_columnconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(inner, text="Trip Details", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#0F172A").grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # -------------------- Variables / controls --------------------
        DAYS_OPTIONS = ["1", "3", "5", "7", "10", "14"]
        PEOPLE_OPTIONS = [str(i) for i in range(1, 11)]
        # include a "No room" option for day trips
        ROOMS_OPTIONS = ["No room (day trip)", "1", "2", "3", "4", "5"]


        self.days_var = ctk.StringVar(value="3")
        self.people_var = ctk.StringVar(value="2")
        self.rooms_var = ctk.StringVar(value="1")
        self.tier_var = ctk.StringVar(value="Comfortable")
        self.transport_var = ctk.StringVar(value="Bus")
        self.origin_var = ctk.StringVar(value="Dhaka")
        self.destination_var = ctk.StringVar(value="Cox's Bazar")

        # row helper
        self._r = 1
        def add_row(text_label, widget):
            r = self._r
            lbl = ctk.CTkLabel(inner, text=text_label, anchor="w", font=ctk.CTkFont(size=12))
            lbl.grid(row=r, column=0, sticky="w", padx=(6, 10), pady=6)
            widget.grid(row=r, column=1, sticky="ew", padx=(0, 6), pady=6)
            self._r += 1

        # Add dropdowns & option menus
        add_row("Days:", ctk.CTkOptionMenu(inner, values=DAYS_OPTIONS, variable=self.days_var))
        add_row("People:", ctk.CTkOptionMenu(inner, values=PEOPLE_OPTIONS, variable=self.people_var))
        add_row("Rooms:", ctk.CTkOptionMenu(inner, values=ROOMS_OPTIONS, variable=self.rooms_var))
        add_row("Travel Style:", ctk.CTkOptionMenu(inner, values=["budget", "comfortable", "luxury"], variable=self.tier_var))
        add_row("Transport:", ctk.CTkOptionMenu(inner, values=["bus", "train", "air"], variable=self.transport_var))

        # -------------------- custom scrollable dropdowns for districts --------------------
        # helper: create a button that opens a fixed-height scrollable popup listing values
        def make_scroll_dropdown(parent, var: ctk.StringVar, values: list, width=200, popup_height=260):
            # create a button showing current selection
            btn = ctk.CTkButton(parent, text=var.get(), width=width, anchor="w")

            # keep button label in sync with var
            def _update_btn(*_):
                try:
                    btn.configure(text=var.get())
                except Exception:
                    pass
            try:
                var.trace_add("write", _update_btn)
            except Exception:
                # older tkinter fallback
                try:
                    var.trace("w", _update_btn)
                except Exception:
                    pass

            def open_popup():
                # top-level popup (use CTkToplevel if available)
                try:
                    popup = ctk.CTkToplevel(self)
                except Exception:
                    import tkinter as tk
                    popup = tk.Toplevel(self)
                popup.overrideredirect(True)
                popup.transient(self)

                # calculate popup position below the button
                bx = btn.winfo_rootx()
                by = btn.winfo_rooty() + btn.winfo_height()
                popup.geometry(f"+{bx}+{by}")

                # closing helper
                def close_popup(e=None):
                    try:
                        popup.grab_release()
                    except Exception:
                        pass
                    try:
                        popup.destroy()
                    except Exception:
                        pass

                # frame + scrollable area inside popup
                pop_frame = ctk.CTkFrame(popup, fg_color="white")
                pop_frame.pack(fill="both", expand=True)

                scroll = ctk.CTkScrollableFrame(pop_frame, fg_color="transparent", width=width, height=popup_height)
                scroll.pack(fill="both", expand=True, padx=6, pady=6)

                # create item buttons
                def on_select(val):
                    var.set(val)
                    close_popup()

                for val in values:
                    item = ctk.CTkButton(scroll, text=val, anchor="w", height=32,
                                         command=lambda v=val: on_select(v))
                    item.pack(fill="x", pady=2, padx=2)

                # focus & grab to keep popup open until user clicks outside or presses Escape
                try:
                    popup.grab_set()
                except Exception:
                    pass
                popup.focus_force()

                # close on Escape
                popup.bind("<Escape>", close_popup)

                try:
                    popup.grab_set()
                except Exception:
                    pass

                # If popup loses focus (user clicked elsewhere), close it
                popup.bind("<FocusOut>", lambda e: close_popup())
                # Also ensure closing via window manager
                try:
                    popup.protocol("WM_DELETE_WINDOW", close_popup)
                except Exception:
                    pass

            btn.configure(command=open_popup)
            return btn

        origin_dropdown = make_scroll_dropdown(inner, self.origin_var, self.DISTRICTS, width=200, popup_height=260)
        
        try:
            attractions_list = load_attractions() or []
            place_names = [a.get("name", "Unknown") for a in attractions_list]
            if not place_names:
                place_names = ["No attractions available"]
        except Exception:
            place_names = ["No attractions available"]

        # set a sensible default if one not already chosen
        if not self.destination_var.get():
            self.destination_var.set(place_names[0])

        # create popup dropdown with attraction names
        destination_dropdown = make_scroll_dropdown(inner, self.destination_var, place_names, width=260, popup_height=320)

        add_row("Starting District:", origin_dropdown)
        add_row("Destination:", destination_dropdown)

        # -------------------- Generate & Save buttons --------------------
        gen_btn = ctk.CTkButton(inner, text="Generate Itinerary", fg_color="#2563EB", hover_color="#1D4ED8",
                                height=40, command=self.on_generate)
        gen_btn.grid(row=self._r, column=0, columnspan=2, pady=(12, 6), padx=8, sticky="ew")
        self._r += 1

        self._r += 1

        # ---------- TOP RIGHT: Cost Summary ----------
        summary_card = ctk.CTkFrame(main, fg_color="#FFFFFF", corner_radius=12)
        summary_card.grid(row=0, column=1, sticky="nsew", padx=(8, 6), pady=(0, 10))
        summary_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(summary_card, text="Cost Summary", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        # styled summary labels
        self.summary_total_lbl = ctk.CTkLabel(summary_card, text="Grand total: —", font=ctk.CTkFont(size=16, weight="bold"), text_color="#0F172A")
        self.summary_total_lbl.pack(anchor="w", padx=12, pady=(6, 2))

        self.summary_sub_lbl = ctk.CTkLabel(summary_card, text="(Estimated breakdown below)", font=ctk.CTkFont(size=11), text_color="#6B7280")
        self.summary_sub_lbl.pack(anchor="w", padx=12, pady=(0, 6))

        self.summary_details_lbl = ctk.CTkLabel(summary_card, text="No plan yet", justify="left", wraplength=260, text_color="#374151", font=ctk.CTkFont(size=11))
        self.summary_details_lbl.pack(anchor="w", padx=12, pady=(0, 12), fill="both", expand=False)

        # ---------- BOTTOM: Results area (spans both columns) ----------
        results_frame = ctk.CTkFrame(main, fg_color="transparent")
        results_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=6, pady=(6, 0))
        results_frame.grid_columnconfigure(0, weight=3)
        results_frame.grid_columnconfigure(1, weight=1)

        # left: scrollable day-cards area
        left_results = ctk.CTkScrollableFrame(results_frame, fg_color="#FFFFFF", corner_radius=12)
        left_results.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=6)
        left_results.grid_columnconfigure(0, weight=1)

        self.it_scroll = left_results
        # fonts for itinerary rendering
        self._it_heading_font = ctk.CTkFont(size=13, weight="bold")
        self._it_text_font = ctk.CTkFont(size=11)

        # right: quick actions
        right_panel = ctk.CTkFrame(results_frame, fg_color="#FFFFFF", corner_radius=12)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=6)
        ctk.CTkLabel(right_panel, text="Quick Actions", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(12, 6))
        ctk.CTkButton(right_panel, text="Export PDF", width=140, command=self.export_plan_pdf).pack(anchor="w", padx=12, pady=(6,4))
        ctk.CTkButton(right_panel, text="Show on Map", width=140, command=self.on_show_map_quick).pack(anchor="w", padx=12, pady=(4,6))

        # last plan container
        self.last_plan = None

    # ----------------- generation & rendering -----------------
    def on_generate(self):
        # parse inputs and validate
        try:
            days = int(self.days_var.get())
            people = int(self.people_var.get())
            rooms = int(self.rooms_var.get())
            tier = self.tier_var.get()
            transport = self.transport_var.get()
            origin = self.origin_var.get().strip()
            destination = self.destination_var.get().strip()
        except Exception:
            self._show_message("Please enter valid values for days, people and rooms.")
            return

        if days < 1 or days > 14:
            self._show_message("Days must be between 1 and 14.")
            return
        if people < 1:
            self._show_message("People must be at least 1.")
            return

        # load attractions and try to match dest/coords
        attractions = load_attractions() or []
        dest_attractions = []
        dest_coords = None
        q = destination.strip().lower()

        # 1) try direct match by name/location/slug
        for a in attractions:
            if any(q in (str(a.get(field) or "")).lower() or (str(a.get(field) or "")).lower() in q
                for field in ("name", "location", "slug")):
                dest_attractions.append(a)
                if not dest_coords and a.get("coords"):
                    try:
                        dest_coords = tuple(a.get("coords"))
                    except Exception:
                        pass

        # 2) fallback to the CITY_COORDS resolver (covers "Sundarbans", typos etc.)
        if not dest_coords:
            try:
                dest_coords = resolve_city_coords(destination, attractions=attractions)
            except Exception:
                dest_coords = None


        # origin coords (match attractions then resolver)
        origin_coords = None
        if origin:
            for a in attractions:
                if origin.lower() in ((a.get("name") or "").lower() + " " + (a.get("location") or "").lower()):
                    if a.get("coords"):
                        origin_coords = tuple(a.get("coords"))
                        break
            if not origin_coords:
                try:
                    origin_coords = resolve_city_coords(origin, attractions=attractions)
                except Exception:
                    origin_coords = None

        # compute costs
        cost_summary = {}
        if origin_coords and dest_coords:
            try:
                cost_summary = compute_trip_estimate(
                    origin_coords=origin_coords,
                    dest_coords=dest_coords,
                    mode=transport,
                    people=people,
                    days=days,
                    accommodation_tier=tier,
                    rooms=rooms,
                    food_tier=tier
                )
            except Exception as e:
                cost_summary = {"error": f"Cost computation failed: {e}"}
        else:
            # compute accommodation + food + local transport fallback
            nights = max(0, days)  # nights may be 0 when rooms==0
            if rooms == 0:
                accom = {"per_night": 0, "nights": 0, "total": 0}
            else:
                accom = accommodation_cost(tier, nights=max(1, days), rooms=rooms, city_multiplier=1.0)

            food = food_cost(tier, people=people, days=days)
            local_transport = 200 * people * days

            # ensure identical keys used below
            subtotal = accom.get("total", 0) + food.get("total", 0) + local_transport
            contingency = round(subtotal * 0.08, 2)
            grand_total = round(subtotal + contingency, 2)
            cost_summary = {
                "note": "Transport estimate skipped (missing origin/destination coordinates).",
                "accommodation": accom,
                "food": food,
                "local_transport": local_transport,
                "subtotal": subtotal,
                "contingency": contingency,
                "grand_total": grand_total
            }

        preset = get_preset_for_destination(destination)
        if preset:
            plan = preset_to_plan(preset, days)
        else:
            plan = self._build_simple_plan(days, dest_attractions or attractions, people)


        result_obj = {
            "requested": {"days": days, "people": people, "rooms": rooms, "tier": tier,
                          "transport": transport, "origin": origin, "destination": destination},
            "costs": cost_summary,
            "plan": plan
        }
        self.last_plan = result_obj
        self._render_result(result_obj)

    def _build_simple_plan(self, days: int, candidates: list, people: int):
        # sort by rating/popularity then take up to days*3 stops
        def score(a):
            try:
                return float(a.get("rating", 0)) if a.get("rating") is not None else 0
            except Exception:
                return 0
        pool = sorted(candidates, key=score, reverse=True)
        max_stops = min(len(pool), days * 3)
        selected = pool[:max_stops]
        per_day = []
        ptr = 0
        for d in range(days):
            stops_for_day = []
            hour = 9
            for s in range(3):
                if ptr >= len(selected):
                    break
                a = selected[ptr]
                ptr += 1
                stops_for_day.append({
                    "time": f"{hour:02d}:00",
                    "name": a.get("name"),
                    "location": a.get("location"),
                    "desc": (a.get("desc") or a.get("summary") or "")[:120],
                    "entry_fee": a.get("avg_entry_fee") or a.get("avg_fee") or 0
                })
                hour += 3
            per_day.append({"day": d + 1, "stops": stops_for_day})
        return per_day

    def _render_result(self, data: dict):
        """Render plan into card-like day rows and update styled cost summary."""
        # clear old cards
        try:
            for child in list(self.it_scroll.winfo_children()):
                child.destroy()
        except Exception:
            pass

        req = data.get("requested", {})
        costs = data.get("costs", {})
        plan = data.get("plan", [])

        # header summary at top of itinerary column
        title_frame = ctk.CTkFrame(self.it_scroll, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(4, 6), padx=6)
        title_lbl = ctk.CTkLabel(title_frame,
                                 text=f"{req.get('days')}d · {req.get('people')}p · {req.get('destination')}",
                                 font=self._it_heading_font,
                                 text_color="#0F172A")
        title_lbl.pack(anchor="w")

        row_index = 1
        if not plan:
            empty_lbl = ctk.CTkLabel(self.it_scroll, text="No itinerary available.", font=self._it_text_font, text_color="#6B7280")
            empty_lbl.grid(row=row_index, column=0, sticky="w", padx=8, pady=6)
            row_index += 1
        else:
            for d in plan:
                day_card = ctk.CTkFrame(self.it_scroll, fg_color="#F8FAFF", corner_radius=10)
                day_card.grid(row=row_index, column=0, sticky="ew", padx=8, pady=(6, 4))
                day_card.grid_columnconfigure(0, weight=1)

                hdr = ctk.CTkLabel(day_card, text=f"Day {d['day']}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#0F172A")
                hdr.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

                r = 1
                for s in d.get("stops", []):
                    stop_frame = ctk.CTkFrame(day_card, fg_color="transparent")
                    stop_frame.grid(row=r, column=0, sticky="ew", padx=10, pady=2)
                    stop_frame.grid_columnconfigure(1, weight=1)

                    time_lbl = ctk.CTkLabel(stop_frame, text=s.get("time", ""), width=72, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563EB")
                    time_lbl.grid(row=0, column=0, sticky="w")

                    name_lbl = ctk.CTkLabel(stop_frame, text=s.get("name", ""), anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
                    name_lbl.grid(row=0, column=1, sticky="w", padx=(8, 0))

                    if s.get("desc"):
                        desc_lbl = ctk.CTkLabel(day_card, text=s.get("desc"), font=self._it_text_font, text_color="#475569", wraplength=620, justify="left")
                        desc_lbl.grid(row=r + 1, column=0, sticky="w", padx=(12, 10), pady=(0, 6))
                        r += 1

                    fee = s.get("entry_fee", 0)
                    if fee:
                        fee_lbl = ctk.CTkLabel(day_card, text=f"Entry: {fee} per person", font=ctk.CTkFont(size=10), text_color="#6B7280")
                        fee_lbl.grid(row=r + 1, column=0, sticky="w", padx=(12, 10), pady=(0, 6))
                        r += 1

                    r += 1

                row_index += 1

        # ---- Update cost summary panel ----
        details_lines = []
        if isinstance(costs, dict):
            if costs.get("note"):
                details_lines.append(costs["note"])
            if costs.get("transport"):
                t = costs["transport"]
                details_lines.append(f"Transport: {t.get('mode')} • {t.get('distance_km')} km")
                details_lines.append(f"Per person (one-way): {t.get('per_personeway')}")
                details_lines.append(f"Total (roundtrip): {t.get('total_roundtrip')}")
            if costs.get("accommodation"):
                a = costs["accommodation"]
                details_lines.append(f"Accommodation: {a.get('per_night')}/night · nights: {a.get('nights')}")
                details_lines.append(f"Total accom: {a.get('total')}")
            if costs.get("food"):
                f = costs["food"]
                details_lines.append(f"Food: {f.get('per_person_day')}/p/day · total: {f.get('total')}")
            if costs.get("local_transport") is not None:
                details_lines.append(f"Local transport: {costs.get('local_transport')}")
            if costs.get("subtotal") is not None:
                details_lines.append(f"Subtotal: {costs.get('subtotal')}")
            if costs.get("contingency") is not None:
                details_lines.append(f"Contingency: {costs.get('contingency')}")
            if costs.get("grand_total") is not None:
                grand = costs.get("grand_total")
                # emphasize grand total
                try:
                    self.summary_total_lbl.configure(text=f"Grand total: {grand}", text_color="#0B5FFF")
                except Exception:
                    self.summary_total_lbl.configure(text=f"Grand total: {grand}")
        else:
            details_lines.append("No cost data available.")

        self.summary_details_lbl.configure(text="\n".join(details_lines))

    # ----------------- small utilities -----------------
    def _show_message(self, text: str):
        popup = ctk.CTkLabel(self, text=text, text_color="white", fg_color="#DC2626")
        popup.place(relx=0.5, rely=0.96, anchor="s")
        self.after(3000, popup.destroy)


    def export_plan_pdf(self):
        """Export current last_plan to a readable PDF, ask user for save location."""
        if not getattr(self, "last_plan", None):
            self._show_message("Generate a plan first.")
            return

        try:
            from tkinter import filedialog as tkf
            suggested = f"{(self.last_plan.get('requested',{}).get('destination') or 'itinerary').replace(' ', '_')}.pdf"
            path = tkf.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=suggested)
            if not path:
                return

            # call helper
            export_itinerary_to_pdf(self.last_plan, path, title=f"Itinerary — {self.last_plan.get('requested',{}).get('destination','')}")
            self._show_message("PDF exported.")
        except Exception as e:
            self._show_message(f"PDF export failed: {e}")



    def on_show_map_quick(self):
        origin = self.origin_var.get().strip()
        dest = self.destination_var.get().strip()
        # try to resolve coords (reuse your resolver)
        attractions = load_attractions() or []
        o_coords = resolve_city_coords(origin, attractions=attractions)
        d_coords = resolve_city_coords(dest, attractions=attractions)
        dist = open_google_maps_directions(origin, dest, origin_coords=o_coords, dest_coords=d_coords)
        if dist is not None:
            self._show_message(f"Distance ≈ {dist} km — opening Google Maps.")
        else:
            self._show_message("Opening Google Maps (coords not available for distance calc).")