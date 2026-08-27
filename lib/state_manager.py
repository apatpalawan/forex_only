"""
State manager - กันแจ้งเตือนซ้ำแท่ง M1 เดิม และคุมจำนวนแจ้งเตือนต่อคู่ต่อวัน
เก็บเป็น state.json แล้ว commit กลับเข้า repo ผ่าน GitHub Actions step (เหมือน sideway-breakout bot เดิม)
"""

import json
import os
from datetime import datetime, timezone
import config


def load_state() -> dict:
    if not os.path.exists(config.STATE_FILE):
        return {}
    try:
        with open(config.STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict):
    with open(config.STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def already_alerted(state: dict, symbol: str, trigger_time: str) -> bool:
    entry = state.get(symbol)
    return bool(entry) and entry.get("last_trigger_time") == trigger_time


def alerts_today(state: dict, symbol: str) -> int:
    entry = state.get(symbol)
    if not entry:
        return 0
    today = datetime.now(timezone.utc).date().isoformat()
    if entry.get("date") != today:
        return 0
    return entry.get("count", 0)


def record_alert(state: dict, symbol: str, trigger_time: str):
    today = datetime.now(timezone.utc).date().isoformat()
    entry = state.get(symbol, {})
    count = entry.get("count", 0) if entry.get("date") == today else 0
    state[symbol] = {
        "last_trigger_time": trigger_time,
        "date": today,
        "count": count + 1,
    }
