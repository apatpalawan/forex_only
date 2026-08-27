"""
News filter (optional, ปิดไว้โดย default - เปิดใน config.NEWS_FILTER_ENABLED)
เช็ค Forex Factory calendar เดียวกับที่ news_reaction_bot ใช้ - ถ้ามีข่าว High impact
ของสกุลเงินในคู่นั้นใกล้เข้ามา ให้ระงับการแจ้งเตือน M1 ชั่วคราว กันสัญญาณหลอกช่วง spike ข่าว
"""

from datetime import datetime, timezone, timedelta
import config

try:
    import requests
except ImportError:
    requests = None

_CACHE = {"data": None, "fetched_at": None}


def _load_calendar():
    if not requests:
        return []
    now = datetime.now(timezone.utc)
    if _CACHE["data"] is not None and _CACHE["fetched_at"] and (now - _CACHE["fetched_at"]).seconds < 900:
        return _CACHE["data"]
    try:
        resp = requests.get(config.FOREX_FACTORY_JSON_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        _CACHE["data"] = data
        _CACHE["fetched_at"] = now
        return data
    except Exception as e:
        print(f"[news_filter] calendar fetch failed: {e}")
        return _CACHE["data"] or []


def is_blocked_by_news(symbol: str) -> bool:
    if not config.NEWS_FILTER_ENABLED:
        return False

    currencies = _symbol_to_currencies(symbol)
    if not currencies:
        return False

    events = _load_calendar()
    now = datetime.now(timezone.utc)
    before = timedelta(minutes=config.NEWS_BLOCK_MINUTES_BEFORE)
    after = timedelta(minutes=config.NEWS_BLOCK_MINUTES_AFTER)

    for ev in events:
        if ev.get("impact") != "High":
            continue
        if ev.get("country") not in currencies:
            continue
        try:
            ev_time = datetime.fromisoformat(ev["date"].replace("Z", "+00:00"))
        except Exception:
            continue
        if (ev_time - before) <= now <= (ev_time + after):
            return True
    return False


def _symbol_to_currencies(symbol: str):
    base = symbol.replace("=X", "").upper()
    if base == "XAUUSD":
        return {"USD"}
    if len(base) == 6:
        return {base[:3], base[3:]}
    return set()
