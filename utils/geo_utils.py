# utils/geo_utils.py
import math
import webbrowser


def haversine_km(coord1, coord2):
    """
    Calculate great-circle distance between two (lat, lon) points in KM.
    """
    R = 6371.0
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def open_google_maps_directions(
    origin_text: str,
    dest_text: str,
    origin_coords=None,
    dest_coords=None
):
    """
    Open Google Maps directions.
    Returns distance in KM if coords are provided, else None.
    """
    origin_q = origin_text or ""
    dest_q = dest_text or ""

    if origin_coords and dest_coords:
        origin_q = f"{origin_coords[0]},{origin_coords[1]}"
        dest_q = f"{dest_coords[0]},{dest_coords[1]}"
        distance = round(haversine_km(origin_coords, dest_coords), 2)
    else:
        distance = None

    url = f"https://www.google.com/maps/dir/{origin_q}/{dest_q}/"
    webbrowser.open(url)
    return distance
