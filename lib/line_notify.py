"""
ส่งข้อความเข้า LINE Official Account ผ่าน Messaging API
- ถ้ามี LINE_TARGET_IDS -> push ไปหาแต่ละ id (comma-separated)
- ถ้าไม่มี -> broadcast ไปหาทุกคนที่แอดเพื่อน OA
- ถ้าไม่มี LINE_CHANNEL_ACCESS_TOKEN -> print ออก console แทน (โหมดทดสอบ)
"""
import requests

PUSH_URL = "https://api.line.me/v2/bot/message/push"
BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"


def _post(url: str, token: str, payload: dict) -> bool:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    ok = 200 <= resp.status_code < 300
    if not ok:
        print(f"[line_notify] send failed ({resp.status_code}): {resp.text}")
    return ok


def send_message(text: str, config) -> bool:
    token = config.LINE_CHANNEL_ACCESS_TOKEN
    target_ids = [t.strip() for t in (config.LINE_TARGET_IDS or "").split(",") if t.strip()]

    if not token:
        print(f"[line_notify][DRY RUN - no token] {text}")
        return True

    message = {"type": "text", "text": text}

    if target_ids:
        all_ok = True
        for target_id in target_ids:
            payload = {"to": target_id, "messages": [message]}
            all_ok = _post(PUSH_URL, token, payload) and all_ok
        return all_ok

    payload = {"messages": [message]}
    return _post(BROADCAST_URL, token, payload)
