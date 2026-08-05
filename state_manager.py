"""
เก็บ/โหลดสถานะ (กรอบ sideway ล่าสุดของแต่ละคู่เงิน, สถานะว่าส่งสัญญาณ breakout ไปแล้วหรือยัง ฯลฯ)
ลง state.json แล้ว workflow จะ commit ไฟล์นี้กลับเข้า repo ทุกครั้งที่รัน
เพื่อให้ job ที่รันครั้งถัดไป (หรือ workflow อื่น) อ่านสถานะต่อเนื่องกันได้
"""
import json
import os


def load_state(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(path, state):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
