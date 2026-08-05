# core/config.py
import os
import json
from pathlib import Path

def get_resource_path(filename):
    """Get the absolute path to a resource in the assets directory (Bolt Optimization v3)."""
    # Synchronized Hyper-Robust discovery logic
    script_dir = Path(__file__).resolve().parent # core/
    cwd = Path.cwd()
    
    candidates = [
        script_dir.parent / "assets", # v2/assets
        cwd / "v2" / "assets",
        cwd / "assets",
        script_dir.parent.parent / "assets"
    ]
    
    for d in candidates:
        abs_d = d.resolve()
        if abs_d.exists() and abs_d.is_dir():
            target_path = abs_d / filename
            if target_path.exists():
                return str(target_path)
             
    # Default fallback if nothing found
    return str((script_dir.parent / "assets" / filename).resolve())

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
