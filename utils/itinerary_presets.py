import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PLANS_DIR = os.path.join(DATA_DIR, "plans")

def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def list_presets():
    """Return list of preset plan slugs (filenames without .json)."""
    if not os.path.isdir(PLANS_DIR):
        return []
    files = [f for f in os.listdir(PLANS_DIR) if f.endswith(".json")]
    return [os.path.splitext(f)[0] for f in files]

def load_preset(slug: str):
    """Load preset JSON by slug, return dict or None."""
    if not slug:
        return None
    path = os.path.join(PLANS_DIR, f"{slug}.json")
    return _load_json(path)

def get_preset_for_destination(destination_name: str):
    """
    Try to find a preset whose slug or name matches destination_name.
    Returns the preset dict or None.
    """
    if not destination_name:
        return None
    q = destination_name.strip().lower()
    for slug in list_presets():
        p = load_preset(slug)
        if not p:
            continue
        # match by slug, name, or presence of destination in name
        name = (p.get("name") or "").lower()
        if slug.lower() in q or q in slug.lower() or q in name or name in q:
            return p
    return None

# small helper to extract per-day data trimmed/padded to requested days
def preset_to_plan(preset: dict, days: int):
    if not preset or "days_data" not in preset:
        return [{"day": d+1, "stops": []} for d in range(days)]
    out = []
    days_data = preset.get("days_data", [])
    for i in range(days):
        if i < len(days_data):
            entry = days_data[i].copy()
            entry["day"] = i + 1
            out.append(entry)
        else:
            out.append({"day": i + 1, "stops": []})
    return out
