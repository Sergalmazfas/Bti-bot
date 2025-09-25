from typing import Dict, Any

def calculate_prices(registry_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    area = float(registry_data.get("area_m2") or 0)
    base_price_per_m2 = float(registry_data.get("base_price_per_m2") or 30000)
    base = area * base_price_per_m2

    # Measurements adjustment uses market average
    market_avg_per_m2 = market_data.get("average_price_per_m2") or base_price_per_m2
    measurements = base * (market_avg_per_m2 / base_price_per_m2)

    # Spec assignment blend with median
    median_per_m2 = market_data.get("median_price_per_m2") or market_avg_per_m2
    spec = 0.7 * base + 0.3 * (median_per_m2 * area)

    return {
        "tech_passport": {"price": round(base, 2), "basis": "registry"},
        "measurements": {"price": round(measurements, 2), "basis": "market-adjusted"},
        "spec_assignment": {"price": round(spec, 2), "basis": "median-blend"}
    }
