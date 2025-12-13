# itinerary_utils.py
import math
import sqlite3
import datetime
from typing import Tuple, Dict, Any
from config import DB_PATH    # we will create this tiny config file

# ---------------- Default rate tables (BDT) ----------------

TRANSPORT_RATES_PER_KM = {
    "bus": 1.2,
    "train": 0.9,
    "air": 6.0,
}
AIR_FIXED_FEE_PER_PASSENGER = 800

ACCOMMODATION_BASE = {
    "budget": 1200,
    "comfortable": 3600,
    "luxury": 9000,
}

FOOD_PER_PERSON_PER_DAY = {
    "budget": 300,
    "comfortable": 800,
    "luxury": 2000,
}

CITY_COORDS = {
    "bagerhat": (22.6580, 89.7853),
    "bandarban": (22.1953, 92.2180),
    "barishal": (22.7010, 90.3535),
    "barguna": (22.1591, 90.1256),
    "bhola": (22.6859, 90.6486),
    "bogura": (24.8481, 89.3720),
    "brahmanbaria": (23.9570, 91.1110),
    "chandpur": (23.2510, 90.8510),
    "chapai nawabganj": (24.5965, 88.2773),
    "chattogram": (22.3569, 91.7832),
    "chuadanga": (23.6400, 88.8410),
    "cox's bazar": (21.4272, 92.0058),
    "cumilla": (23.4607, 91.1809),
    "dhaka": (23.8103, 90.4125),
    "dinajpur": (25.6270, 88.6332),
    "faridpur": (23.6071, 89.8420),
    "feni": (23.0159, 91.3976),
    "gaibandha": (25.3288, 89.5283),
    "gazipur": (23.9999, 90.4203),
    "gopalganj": (23.0050, 89.8266),
    "habiganj": (24.3740, 91.4125),
    "jamalpur": (24.9375, 89.9370),
    "jashore": (23.1634, 89.2185),
    "jhalokathi": (22.6406, 90.1987),
    "jhenaidah": (23.5448, 89.1535),
    "joypurhat": (25.0947, 89.0945),
    "khagrachhari": (23.1193, 91.9847),
    "khulna": (22.8456, 89.5403),
    "kishoreganj": (24.4449, 90.7766),
    "kurigram": (25.8054, 89.6362),
    "kushtia": (23.9013, 89.1205),
    "lakshmipur": (22.9420, 90.8312),
    "lalmonirhat": (25.9923, 89.2847),
    "madaripur": (23.1640, 90.1893),
    "magura": (23.4870, 89.4195),
    "manikganj": (23.8617, 90.0003),
    "meherpur": (23.7622, 88.6318),
    "moulvibazar": (24.4829, 91.7777),
    "munshiganj": (23.5422, 90.5305),
    "mymensingh": (24.7471, 90.4203),
    "narail": (23.1725, 89.5120),
    "narayanganj": (23.6238, 90.5000),
    "narsingdi": (23.9200, 90.7183),
    "natore": (24.4206, 89.0000),
    "naogaon": (24.8073, 88.9460),
    "narail": (23.1725, 89.5120),
    "natore": (24.4206, 89.0000),
    "nawabganj": (24.5965, 88.2773),  # alias of Chapai Nawabganj if needed
    "netrokona": (24.8835, 90.7279),
    "nilphamari": (25.9310, 88.8560),
    "noakhali": (22.8696, 91.0994),
    "pabna": (24.0064, 89.2372),
    "panchagarh": (26.3411, 88.5542),
    "patuakhali": (22.3596, 90.3293),
    "pirojpur": (22.5794, 89.9720),
    "rajbari": (23.7574, 89.6447),
    "rajshahi": (24.3636, 88.6241),
    "rangamati": (22.6316, 92.2185),
    "rangpur": (25.7439, 89.2752),
    "satkhira": (22.7185, 89.0705),
    "shariatpur": (23.2423, 90.4348),
    "sherpur": (25.0188, 90.0098),
    "sirajganj": (24.4575, 89.7083),
    "sunamganj": (25.0658, 91.3950),
    "sylhet": (24.8949, 91.8687),
    "tangail": (24.2513, 89.9180),
    "thakurgaon": (26.0410, 88.4690),
    "sundarbans": (21.9497, 89.1833),      # central approximate coords for the Sundarbans
    "sundarban": (21.9497, 89.1833),       # alternate spelling
    "cox's bazar": (21.4272, 92.0058),     # ensure Cox's Bazar present
    "coxs bazar": (21.4272, 92.0058),
}



def resolve_city_coords(name: str, attractions: list | None = None):
    """
    Best-effort resolve a human-entered city/place name to (lat, lon) tuple.
    - First looks through provided attractions (if any) for an exact or substring match and returns their coords.
    - Then falls back to CITY_COORDS dictionary matching (case-insensitive, substring).
    - Returns None if not found.
    """
    if not name:
        return None

    q = name.strip().lower()

    # 1) try attractions list first (if provided)
    if attractions:
        for a in attractions:
            # check many fields
            for field in ("slug", "name", "location"):
                val = (a.get(field) or "").lower()
                if q == val or q in val or val in q:
                    coords = a.get("coords") or a.get("latlon") or a.get("coordinates")
                    if coords:
                        try:
                            return tuple(coords)
                        except Exception:
                            pass

    # 2) fallback to CITY_COORDS by substring match
    for city_key, coords in CITY_COORDS.items():
        if city_key in q or q in city_key:
            return coords

    # no match
    return None


LOCAL_TRANSPORT_PER_PERSON_PER_DAY = 200
CONTINGENCY_RATE = 0.08  # 8%


# ---------------- Database table for saved itineraries ----------------

def ensure_saved_itineraries_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saved_itineraries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            title TEXT,
            created_at TEXT,
            plan_json TEXT
        )
    """)
    conn.commit()
    conn.close()


# ---------------- Haversine distance ----------------

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2)**2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ---------------- Transport cost estimator ----------------

def transport_cost_km_mode(
    distance_km: float,
    mode: str,
    passengers: int = 1,
    round_trip: bool = True
) -> Dict[str, Any]:

    mode = mode.lower()
    if mode not in TRANSPORT_RATES_PER_KM:
        raise ValueError(f"Unknown transport mode: {mode}")

    per_km = TRANSPORT_RATES_PER_KM[mode]
    per_person_oneway = distance_km * per_km

    if mode == "air":
        per_person_oneway += AIR_FIXED_FEE_PER_PASSENGER

    total_oneway = per_person_oneway * passengers
    total = total_oneway * (2 if round_trip else 1)

    return {
        "mode": mode,
        "distance_km": round(distance_km, 1),
        "per_person_oneway": round(per_person_oneway, 2),
        "total_oneway": round(total_oneway, 2),
        "total_roundtrip": round(total, 2),
        "passengers": passengers,
        "round_trip": round_trip,
    }


# ---------------- Accommodation cost ----------------

def accommodation_cost(
    tier: str,
    nights: int = 1,
    rooms: int = 1,
    city_multiplier: float = 1.0
) -> Dict[str, Any]:

    tier = tier.lower()
    base = ACCOMMODATION_BASE.get(tier)
    if base is None:
        raise ValueError("Unknown accommodation tier")

    per_night = base * city_multiplier
    total = per_night * nights * rooms

    return {
        "tier": tier,
        "per_night": round(per_night, 2),
        "nights": nights,
        "rooms": rooms,
        "total": round(total, 2)
    }


# ---------------- Food cost ----------------

def food_cost(tier: str, people: int = 1, days: int = 1):
    tier = tier.lower()
    per_person_day = FOOD_PER_PERSON_PER_DAY.get(tier)
    if per_person_day is None:
        raise ValueError("Unknown food tier")

    total = per_person_day * people * days

    return {
        "tier": tier,
        "per_person_day": per_person_day,
        "people": people,
        "days": days,
        "total": total,
    }


# ---------------- High-level trip cost aggregator ----------------

def compute_trip_estimate(
    *,
    origin_coords: Tuple[float, float],
    dest_coords: Tuple[float, float],
    mode="bus",
    people=1,
    days=1,
    accommodation_tier="comfortable",
    rooms=1,
    city_multiplier=1.0,
    food_tier="comfortable"
) -> Dict[str, Any]:

    d_km = haversine_km(
        origin_coords[0], origin_coords[1],
        dest_coords[0], dest_coords[1]
    )

    transport = transport_cost_km_mode(d_km, mode, passengers=people)

    nights = max(1, days)
    accom = accommodation_cost(accommodation_tier, nights, rooms, city_multiplier)
    food = food_cost(food_tier, people, days)

    local_transport = LOCAL_TRANSPORT_PER_PERSON_PER_DAY * people * days

    subtotal = (
        transport["total_roundtrip"]
        + accom["total"]
        + food["total"]
        + local_transport
    )

    contingency = round(subtotal * CONTINGENCY_RATE, 2)
    grand_total = round(subtotal + contingency, 2)

    return {
        "distance_km": round(d_km, 1),
        "transport": transport,
        "accommodation": accom,
        "food": food,
        "local_transport": local_transport,
        "subtotal": round(subtotal, 2),
        "contingency": contingency,
        "grand_total": grand_total,
    }
