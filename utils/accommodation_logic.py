import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ACCOM_DIR = os.path.join(BASE_DIR, "data", "accommodation")


def _slugify(name: str) -> str:
    return name.lower().replace("'", "").replace(" ", "_")


def load_accommodation(destination: str) -> dict:
    slug = _slugify(destination)
    path = os.path.join(ACCOM_DIR, f"{slug}.json")

    if not os.path.exists(path):
        return {"city": destination, "currency": "BDT", "hotels": []}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_hotels(hotels, tier=None, min_price=None, max_price=None):
    results = []

    for h in hotels:
        pmin = h["price_range"]["min"]
        pmax = h["price_range"]["max"]

        if tier and tier != "any" and h.get("tier") != tier:
            continue
        if min_price is not None and pmax < min_price:
            continue
        if max_price is not None and pmin > max_price:
            continue

        results.append(h)

    return results


def estimate_accommodation_cost(hotel: dict, nights: int, rooms: int) -> dict:
    """
    Estimate accommodation cost based on average price.
    """
    if nights <= 0 or rooms <= 0:
        return {
            "per_night": 0,
            "nights": nights,
            "rooms": rooms,
            "total": 0
        }

    price_min = hotel["price_range"]["min"]
    price_max = hotel["price_range"]["max"]

    avg_price = int((price_min + price_max) / 2)
    total = avg_price * nights * rooms

    return {
        "per_night": avg_price,
        "nights": nights,
        "rooms": rooms,
        "total": total
    }



def get_accommodation_results(
    destination: str,
    nights: int,
    rooms: int,
    tier: str,
    min_price: int,
    max_price: int
):
    data = load_accommodation(destination)
    hotels = data.get("hotels", [])

    hotels = filter_hotels(hotels, tier, min_price, max_price)

    results = []
    for h in hotels:
        hotel_copy = h.copy()
        hotel_copy["estimated_cost"] = estimate_accommodation_cost(h, nights, rooms)
        results.append(hotel_copy)

    return results
