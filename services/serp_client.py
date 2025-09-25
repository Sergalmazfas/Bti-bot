import os
import time
import requests
from typing import Dict, Any

SERPRIVER_API_KEY = os.getenv("SERPRIVER_API_KEY")
SERP_BASE = os.getenv("SERP_BASE", "https://serpriver.ru/api")

MAX_RETRIES = 4
BACKOFF = 1.6

class SerpError(Exception):
    pass

def _get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if not SERPRIVER_API_KEY:
        raise SerpError("SERPRIVER_API_KEY is missing")
    url = f"{SERP_BASE}{path}"
    params = {**params, "api_key": SERPRIVER_API_KEY}
    for i in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, timeout=8)
            if r.status_code == 200:
                return r.json() or {}
            if r.status_code in (429, 500, 502, 503):
                time.sleep(BACKOFF ** (i + 1))
                continue
            raise SerpError(f"SERP {r.status_code}: {r.text}")
        except requests.RequestException as e:
            if i == MAX_RETRIES - 1:
                raise SerpError(str(e))
            time.sleep(BACKOFF ** (i + 1))
    return {}

def get_market_aggregates(reg: Dict[str, Any]) -> Dict[str, Any]:
    # Use address/lat/lon/area for filters
    lat = reg.get("lat")
    lon = reg.get("lon")
    area = reg.get("area_m2")
    floors = reg.get("floors")
    payload = {
        "lat": lat,
        "lon": lon,
        "radius_m": 2000,
        "limit": 50,
        "filters": {
            "min_area": max(0, (area or 0) * 0.8) if area else None,
            "max_area": (area or 0) * 1.2 if area else None,
            "floors": floors,
        }
    }
    data = _get("/search.php", payload)
    items = data.get("items", [])
    prices = [x.get("price_per_m2") for x in items if isinstance(x.get("price_per_m2"), (int, float))]
    if prices:
        prices_sorted = sorted(prices)
        median = prices_sorted[len(prices_sorted)//2]
        avg = sum(prices)/len(prices)
        return {"average_price_per_m2": round(avg, 2), "median_price_per_m2": round(median, 2), "sample_size": len(prices)}
    return {"average_price_per_m2": None, "median_price_per_m2": None, "sample_size": 0}
