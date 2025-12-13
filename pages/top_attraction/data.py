import json
import os

ATTRACTIONS_PATH = "data/attractions_augmented.json"

def load_attractions():
    """Load attractions list from JSON file."""
    try:
        with open(ATTRACTIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except FileNotFoundError:
        print("attractions.json not found")
        return []
    except json.JSONDecodeError as e:
        print("Error reading attractions.json:", e)
        return []