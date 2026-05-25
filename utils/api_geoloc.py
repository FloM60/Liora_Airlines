
import pandas as pd
from tqdm import tqdm
from typing import Dict, Any, Optional


import requests

API_GEOLOC = "https://geocoding-api.open-meteo.com/v1/search"



def get_geoloc_from_code(code: str) -> Optional[Dict[str, float]]:
    """Retourne lat/lng pour un code aéroport en string"""
    geoloc = _fetch_geoloc(code)
    if not geoloc:
        pass
    return geoloc

def _fetch_geoloc(code: str) -> Optional[Dict[str, float]]:
    params = {
        'name': code,
        'language': 'fr',
        'format': 'json',
        'count': 1
    }
    try:
        response = requests.get(API_GEOLOC, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        
        if not results:
            return None 
        
        return {
            "lat": results[0]["latitude"], 
            "lng": results[0]["longitude"]
        }
    except requests.RequestException:
        return None


