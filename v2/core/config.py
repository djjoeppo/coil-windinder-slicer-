# core/config.py
import os
import json
import math
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

# Helpers for Fractions, AWG, and Units conversions
def parse_fraction_or_float(val_str):
    """Parses standard decimals, fractions (1/8, 1/32) and mixed numbers (1 1/4) into float."""
    if not val_str:
        return 0.0
    val_str = val_str.strip().replace(",", ".")
    try:
        # Check for mixed numbers like '1 1/4'
        if " " in val_str:
            parts = val_str.split()
            if len(parts) == 2:
                whole = float(parts[0])
                frac = parts[1]
                if "/" in frac:
                    f_num, f_den = frac.split("/")
                    return whole + float(f_num) / float(f_den)
        # Check for simple fraction
        if "/" in val_str:
            f_num, f_den = val_str.split("/")
            return float(f_num) / float(f_den)
        return float(val_str)
    except Exception:
        return 0.0

def mm_to_inch(mm_val):
    return mm_val / 25.4

def inch_to_mm(inch_val):
    return inch_val * 25.4

def awg_to_mm(awg):
    """Standard AWG to millimeter formula: d = 0.127 * 92**((36 - AWG)/39)"""
    try:
        awg_val = float(awg)
        return 0.127 * (92 ** ((36 - awg_val) / 39.0))
    except Exception:
        return 0.0

def mm_to_awg(mm_val):
    """Standard millimeter to AWG formula: AWG = -39 * log92(d / 0.127) + 36"""
    if mm_val <= 0:
        return 40.0 # fallback
    try:
        # log92(x) = ln(x) / ln(92)
        ratio = mm_val / 0.127
        awg_val = -39.0 * (math.log(ratio) / math.log(92.0)) + 36.0
        return round(awg_val, 1)
    except Exception:
        return 40.0
