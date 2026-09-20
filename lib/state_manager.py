"""
อ่าน/บันทึก state.json
เก็บสัญญาณล่าสุดที่เคยแจ้งเตือนไปแล้วต่อ symbol เพื่อกันแจ้งซ้ำสัญญาณเดิมทุกรอบที่สแกน (ทุก 5 นาที)
แจ้งเตือนใหม่ได้เมื่อสัญญาณเปลี่ยน (เช่น จาก buy -> None -> buy อีกครั้ง หรือ buy -> sell)
"""
import json
import os


def load_state(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(path: str, state: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def should_alert(state: dict, symbol: str, signal) -> bool:
    """signal: 'buy' / 'sell' / None. แจ้งเตือนเฉพาะตอนสัญญาณเปลี่ยนไปเป็น buy หรือ sell ใหม่"""
    if signal not in ("buy", "sell"):
        return False
    prev = state.get(symbol, {}).get("last_signal")
    return prev != signal


def update_state(state: dict, symbol: str, signal) -> None:
    if signal in ("buy", "sell"):
        state[symbol] = {"last_signal": signal}
    elif signal is None:
        # เทรนด์/เงื่อนไขหายไปแล้ว เคลียร์ค่าเพื่อให้พร้อมแจ้งเตือนใหม่รอบหน้าถ้าสัญญาณเดิมกลับมาอีก
        if symbol in state:
            state[symbol]["last_signal"] = None
