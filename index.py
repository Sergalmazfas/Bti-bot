import os
import json
import time
from typing import Any, Dict
from utils.validation import is_valid_cadastral
from services.registry_client import get_registry_data
from services.serp_client import get_market_aggregates
from services.pricing_engine import calculate_prices


def _json_response(status_code: int, payload: Dict[str, Any]):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload, ensure_ascii=False)
    }


def handler(event: Dict[str, Any], context: Any):
    start = time.time()
    try:
        body = event.get("body") if isinstance(event, dict) else None
        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8", errors="ignore")
        if isinstance(body, str):
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}
        elif isinstance(event, dict) and "message" in event:
            data = event  # allow direct Telegram-like payload for local tests
        else:
            data = {}

        # Extract cadastral number from text or explicit field
        text = (
            data.get("message", {}).get("text")
            if isinstance(data.get("message"), dict)
            else data.get("text")
        )
        cadnum = data.get("cadastral_number") or (text.strip() if isinstance(text, str) else None)

        if not cadnum or not is_valid_cadastral(cadnum):
            return _json_response(400, {"error": "Некорректный кадастровый номер", "hint": "Формат XX:XX:XXXXXXX:XXXX"})

        # Fetch official registry data
        reg = get_registry_data(cadnum)
        # Fetch market aggregates via SERP/Avito
        market = get_market_aggregates(reg)
        # Calculate 3 prices
        prices = calculate_prices(registry_data=reg, market_data=market)

        elapsed_ms = int((time.time() - start) * 1000)
        return _json_response(200, {
            "cadnum": cadnum,
            "bti": {
                "area_m2": reg.get("area_m2"),
                "floors": reg.get("floors"),
                "walls": reg.get("walls"),
                "year_built": reg.get("year_built"),
                "cadastral_value": reg.get("cadastral_value"),
                "address": reg.get("address"),
            },
            "market": market,
            "prices": prices,
            "meta": {"elapsed_ms": elapsed_ms}
        })
    except Exception as e:
        return _json_response(500, {"error": str(e)})
