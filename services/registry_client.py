import os
import requests
from typing import Dict

REESTR_API_TOKEN = os.getenv("REESTR_API_TOKEN")

BASE_URL = os.getenv("REESTR_BASE_URL", "https://rosreestr.example/api")

class RegistryError(Exception):
    pass

def get_registry_data(cadnum: str) -> Dict:
    if not REESTR_API_TOKEN:
        raise RegistryError("REESTR_API_TOKEN is missing")
    url = f"{BASE_URL}/objects"
    params = {"cadnum": cadnum}
    headers = {"Authorization": f"Bearer {REESTR_API_TOKEN}"}
    r = requests.get(url, params=params, headers=headers, timeout=8)
    if r.status_code != 200:
        raise RegistryError(f"Registry error {r.status_code}: {r.text}")
    j = r.json() or {}
    # Map response -> normalized fields
    return {
        "cadnum": cadnum,
        "area_m2": j.get("area_m2"),
        "floors": j.get("floors"),
        "walls": j.get("walls"),
        "year_built": j.get("year_built"),
        "cadastral_value": j.get("cadastral_value"),
        "address": j.get("address"),
        "lat": j.get("lat"),
        "lon": j.get("lon"),
    }
