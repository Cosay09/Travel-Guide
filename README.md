# 🌍 Travel Guide – Smart Itinerary Planner (Python + CustomTkinter)

A desktop **Travel Guide & Smart Itinerary Planning application** built with **Python** and **CustomTkinter**.

The app helps users explore destinations in **Bangladesh**, plan realistic multi-day trips, understand **transportation routes & costs**, discover **nearby trips and hidden gems**, and export travel plans for offline use.

This project is fully **data-driven**, modular, and designed to demonstrate real-world travel planning logic.

---

## ✨ Core Features

---

## 🏖 Top Attractions
- Visual attraction cards with images and summaries
- Click to open detailed attraction pages
- Rich content support (text / markdown)
- JSON-based data (easy to extend)

---

## 🧭 Custom Itinerary Builder
Users can generate realistic travel plans by selecting:

- Number of days (1, 3, 5, 7, 10, 14)
- Number of travelers (1–10)
- Rooms (including **No room / day trip**)
- Travel style:
  - Budget
  - Comfortable
  - Luxury
- Transport preference:
  - Bus
  - Train
  - Air
- Starting district
- Destination (from available attractions)

### Auto-Generates:
- Day-wise itinerary
- Activity schedules with time blocks
- Logical pacing based on trip length

---

## 💰 Cost Estimation
The planner automatically estimates:

- Transport cost
- Accommodation cost (optional)
- Food cost
- Local transport
- Contingency buffer

Includes:
- Clear category-wise breakdown
- Grand total calculation
- Works fully offline

---

## 🚍 Transportation Guide (Advanced)
A **decision-oriented transportation page** with real-world travel logic:

- Route-based transport options
- Bus, air, ferry, and regional routes
- AC / Non-AC fare ranges
- Popular operators
- Terminal names (e.g. Gabtoli, Sayedabad)
- Travel time estimates
- ⭐ Recommended option per route
- **“Best for” tags** (Budget, Overnight, Fastest, Groups, Scenic)

Designed to help users answer:
> *“How should I actually get there?”*

---

## 🗺 Nearby Trips & Hidden Gems
Discover short trips and lesser-known places:

- Filter by starting city
- Category-based discovery:
  - Nearby Trips
  - Hidden Gems
  - Cultural Spots
  - Nature Escapes
- Distance-aware listings
- One-click Google Maps opening

Perfect for:
- Day trips
- Quick escapes
- Off-the-beaten-path travel

---

## 🗺 Google Maps Integration
- Opens Google Maps with:
  - Route search
  - Destination view
- Works without API keys
- Keeps the app lightweight

---

## 📤 Export & Save
- Export full itinerary as **PDF**
- Save generated plans as **JSON**
- Designed for offline access and sharing

---

## 🧱 Technical Highlights

- Built with **CustomTkinter** (modern UI)
- Clean separation of:
  - UI (pages/)
  - Business logic (utils/)
  - Data (JSON)
- Fully extensible architecture
- No hard-coded routes or destinations
- Offline-first design

---

## 🗂 Project Structure

```text
Travel-Guide/
│
├── assets/                    # Images, icons
├── content/                   # Markdown/text attraction content
├── data/
│   ├── attractions.json
│   ├── nearby_trips.json
│   ├── transportation.json
│   └── accommodation/
│
├── pages/
│   ├── overview.py
│   ├── top_attractions.py
│   ├── itineraries.py
│   ├── transportation.py
│   ├── nearby_trips.py
│   └── accommodation.py
│
├── utils/
│   ├── config.py
│   ├── itinerary_utils.py
│   ├── accommodation_logic.py
│   ├── map_utils.py
│   ├── cost_utils.py
│   ├── pdf_export.py
│   └── page_header.py
│
├── main.py                    # App entry point
├── temp.py                    # Development / testing file
└── README.md
