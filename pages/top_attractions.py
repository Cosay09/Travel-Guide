import customtkinter as ctk
import os
from PIL import Image
from pages.top_attraction.data import load_attractions
import json


class FastScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master=None, scroll_speed: int = 3, **kwargs):
        """
        scroll_speed: how many "steps" per wheel notch.
        1 = default-ish, 3 = faster, 5 = very fast.
        """
        self._scroll_speed = scroll_speed
        super().__init__(master, **kwargs)

    def _mouse_wheel(self, event):
        """Override CTkScrollableFrame default wheel speed (Windows)."""
        # On Windows, event.delta is typically ±120 per notch
        if event.delta != 0:
            steps = int(-event.delta / 120 * self._scroll_speed)
            self._parent_canvas.yview_scroll(steps, "units")


class TopAttractionsPage(FastScrollableFrame):  # or ctk.CTkScrollableFrame
    def __init__(self, parent):
        super().__init__(parent, scroll_speed=4)   # if using FastScrollableFrame

        # ===== Header section =====
        header = ctk.CTkFrame(self, fg_color="#0078D4", corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            header,
            text="🏖 Top Attractions",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="white"
        ).pack(pady=16)

        # ===== Main area background =====
        container = ctk.CTkFrame(self, fg_color="#F3F6FB", corner_radius=0)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        # Load attractions data
        self.attractions = load_attractions()
        if not self.attractions:
            ctk.CTkLabel(container, text="No attractions found.").pack(pady=20)
            return

        # keep cached images alive: list of (normal, zoom) tuples
        self.image_cache = []

        grid_frame = ctk.CTkFrame(container, fg_color="transparent")
        grid_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # 👉 3 columns now
        grid_frame.grid_columnconfigure(0, weight=1, uniform="col")
        grid_frame.grid_columnconfigure(1, weight=1, uniform="col")
        grid_frame.grid_columnconfigure(2, weight=1, uniform="col")

        for idx, attraction in enumerate(self.attractions):
            row = idx // 3
            col = idx % 3
            self.create_card(grid_frame, attraction, row, col)

    # ---------- helper: safe image loader ----------
    @staticmethod
    def _safe_ctk_image(path, size):
        """
        Try to open path with PIL and produce a ctk.CTkImage sized to `size`.
        Returns None on failure.
        """
        if not path:
            return None
        try:
            # normalize path (helps with inconsistent separators)
            path = os.path.normpath(path)
            if not os.path.isabs(path):
                # keep relative paths relative to current working dir
                path = os.path.join(os.getcwd(), path) if not os.path.exists(path) else path

            if not os.path.exists(path):
                # still doesn't exist
                raise FileNotFoundError(f"Image not found: {path}")

            pil_img = Image.open(path).convert("RGBA")
            return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        except Exception as e:
            # don't crash; just return None
            print(f"[TopAttractionsPage] Warning: couldn't load image '{path}': {e}")
            return None

    def create_card(self, parent, attraction, row, col):
        # Larger visual sizes (bigger image)
        CARD_W, CARD_H = 360, 260
        IMG_W, IMG_H = 360, 240
        ZOOM_W, ZOOM_H = 390, 240

        # Underlay shadow for depth
        shadow = ctk.CTkFrame(parent, width=CARD_W+8, height=CARD_H+8, corner_radius=22, fg_color="#E6EEF8")
        shadow.grid(row=row, column=col, padx=10, pady=10, sticky="n")
        shadow.grid_propagate(False)

        card = ctk.CTkFrame(parent, width=CARD_W, height=CARD_H, corner_radius=18, fg_color="#FFFFFF")
        card.grid(row=row, column=col, padx=6, pady=4, sticky="n")
        card.grid_propagate(False)

        img_frame = ctk.CTkFrame(card, fg_color="transparent", width=IMG_W, height=IMG_H)
        img_frame.place(x=0, y=0)
        img_frame.grid_propagate(False)

        img_label = ctk.CTkLabel(img_frame, text="")
        img_label.place(relx=0.5, rely=0.5, anchor="center")
        img_label._current_img = None

        # load images using your safe helper
        normal = self._safe_ctk_image(attraction.get("image", "") or None, (IMG_W, IMG_H))
        zoom = self._safe_ctk_image(attraction.get("image", "") or None, (ZOOM_W, ZOOM_H))

        if normal:
            self.image_cache.append((normal, zoom))
            img_label.configure(image=normal)
            img_label._current_img = normal
        else:
            placeholder = ctk.CTkFrame(img_frame, corner_radius=12, fg_color="#F1F5F9", width=IMG_W-20, height=IMG_H-20)
            placeholder.place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(placeholder, text="No image", font=ctk.CTkFont(size=12)).place(relx=0.5, rely=0.5, anchor="center")
            img_label._current_img = None

        # Gradient-like overlay area at bottom to ensure text readability
        overlay_height = int(IMG_H * 0.30)
        overlay = ctk.CTkFrame(img_frame, fg_color="transparent", width=IMG_W, height=overlay_height)
        overlay.place(relx=0, rely=1.0, anchor="sw")

        # Title (on overlay) - only name + short text (no stars)
        name_text = attraction.get("name", "Unknown")
        title_lbl = ctk.CTkLabel(overlay, text=name_text, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        title_lbl.place(relx=0.03, rely=0.25, anchor="w")

        desc_text = attraction.get("desc", "") or attraction.get("summary", "")
        desc_lbl = ctk.CTkLabel(overlay, text=(desc_text[:120] + ("…" if len(desc_text) > 120 else "")),
                                font=ctk.CTkFont(size=11), anchor="w", wraplength=IMG_W-24)
        desc_lbl.place(relx=0.03, rely=0.65, anchor="w")

        # keep space below overlay for visual separation
        # Back area is already handled in detail; we keep card minimal here.

        # Hover behavior: swap to zoom image and show border
        def on_enter(event=None):
            if zoom is not None and getattr(img_label, "_current_img", None) is not zoom:
                img_label.configure(image=zoom)
                img_label._current_img = zoom
            card.configure(border_width=2, border_color="#0078D4")
            try:
                card.configure(cursor="hand2")
            except Exception:
                pass

        def on_leave(event=None):
            if normal is not None and getattr(img_label, "_current_img", None) is not normal:
                img_label.configure(image=normal)
                img_label._current_img = normal
            card.configure(border_width=0)
            try:
                card.configure(cursor="")
            except Exception:
                pass

        def on_click(event=None):
            app = self.winfo_toplevel()
            if hasattr(app, "show_attraction_page"):
                app.show_attraction_page(attraction)
            else:
                print("[TopAttractionsPage] show_attraction_page not found on app")


        interactive_widgets = (card, img_frame, img_label, title_lbl, desc_lbl)
        for w in interactive_widgets:
            w.bind("<Enter>", on_enter, add="+")
            w.bind("<Leave>", on_leave, add="+")
            w.bind("<Button-1>", on_click, add="+")

