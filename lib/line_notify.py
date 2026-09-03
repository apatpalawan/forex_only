"""
LINE notify - ส่งข้อความสั้นต่อ 1 สัญญาณ (รูปแบบคล้าย format_forex_message ในบอทหลัก)
"""

import requests
import config

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def format_m1_alert(signal: dict) -> str:
    """ข้อความสั้น ประหยัดความยาว - สัญญาณเดียวที่เกิดจาก breakout+volume และ EMA50x100 พร้อมกัน"""
    arrow = "⬆️BUY" if signal["direction"] == "up" else "⬇️SELL"
    sym = signal["symbol"].replace("=X", "").replace("=F", "")
    return (
        f"🎯{sym} {arrow} @ {signal['trigger_price']}\n"
        f"Breakout+Vol+EMA50x100"
    )


def send_line_message(text: str) -> bool:
    if not config.LINE_CHANNEL_ACCESS_TOKEN or not config.LINE_TARGET_IDS:
        print("[line_notify] missing token or target ids, skip send")
        return False

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
    }

    ok_all = True
    for target_id in config.LINE_TARGET_IDS:
        payload = {"to": target_id, "messages": [{"type": "text", "text": text}]}
        try:
            resp = requests.post(LINE_PUSH_URL, headers=headers, json=payload, timeout=10)
            if resp.status_code != 200:
                print(f"[line_notify] FAILED to {target_id}: {resp.status_code} {resp.text}")
                ok_all = False
        except Exception as e:
            print(f"[line_notify] error sending to {target_id}: {e}")
            ok_all = False
    return ok_all
