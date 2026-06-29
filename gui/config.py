# config.py
import os
import json

def load_translations():
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, "languages.json")
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Fout bij laden van talenbestand: {e}")
        return {}

TRANSLATIONS = load_translations()