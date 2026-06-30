# core/config.py
import os
import json

def get_resource_path(filename):
    """Get the absolute path to a resource in the assets directory."""
    # Assuming this file is in core/ and assets/ is in the root
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, "assets", filename)

def load_json(filename):
    path = get_resource_path(filename)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return {}

TRANSLATIONS = load_json("languages.json")
MACHINE_SETTINGS = load_json("machine_settings.json")
MATERIALS = load_json("materials.json")
