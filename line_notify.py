"""
ส่งข้อความเข้า LINE Official Account ผ่าน LINE Messaging API
- ถ้าตั้งค่า LINE_TARGET_IDS (user id / group id คั่นด้วย comma) จะใช้ push API ส่งเฉพาะเป้าหมายนั้น
- ถ้าไม่ตั้งค่า จะใช้ broadcast API ส่งไปหาทุกคนที่แอดเพื่อน OA ไว้

หมายเหตุ: LINE จำกัดความยาวข้อความที่ 5000 หน่วย UTF-16 ต่อข้อความ (ไม่ใช่จำนวนตัวอักษร Python)
emoji แบบ supplementary-plane (เช่น 💥🚀) กิน 2 หน่วย UTF-16 ต่อตัว ถ้าตัดข้อความด้วย
Python code point เฉยๆ (text[:4900]) จะนับผิดและอาจยังเกินลิมิตจริงของ LINE อยู่ดี
ฟังก์ชันนี้เลยนับความยาวแบบ UTF-16 จริง และแบ่งข้อความยาวเป็นหลาย push message แทนการตัดทิ้ง
"""
import requests
import config

PUSH_URL = "https://api.line.me/v2/bot/message/push"
BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"

LINE_LIMIT_UTF16 = 4900  # เผื่อ buffer จากลิมิตจริง 5000 หน่วยของ LINE


def _headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
    }


def _utf16_len(s):
    return len(s.encode("utf-16-le")) // 2


def _split_utf16(text, limit=LINE_LIMIT_UTF16):
    """แบ่งข้อความเป็นหลายก้อน นับความยาวแบบ UTF-16 (ตรงกับที่ LINE ใช้จริง)
    แบ่งตามบรรทัดก่อนเพื่อไม่ตัดข้อความกลางคำ/กลาง emoji"""
    lines = text.split("\n")
    chunks = []
    current = ""

    for line in lines:
        candidate = current + ("\n" if current else "") + line
        if _utf16_len(candidate) > limit and current:
            chunks.append(current)
            current = line
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks or [text]


def _send_one(text):
    target_ids = [t.strip() for t in config.LINE_TARGET_IDS.split(",") if t.strip()]

    if target_ids:
        for uid in target_ids:
            payload = {"to": uid, "messages": [{"type": "text", "text": text}]}
            resp = requests.post(PUSH_URL, headers=_headers(), json=payload, timeout=15)
            if resp.status_code != 200:
                print(f"[ERROR] push ไป {uid} ไม่สำเร็จ: {resp.status_code} {resp.text}")
                return False
    else:
        payload = {"messages": [{"type": "text", "text": text}]}
        resp = requests.post(BROADCAST_URL, headers=_headers(), json=payload, timeout=15)
        if resp.status_code != 200:
            print(f"[ERROR] broadcast ไม่สำเร็จ: {resp.status_code} {resp.text}")
            return False

    return True


def send_line_message(text):
    if not config.LINE_CHANNEL_ACCESS_TOKEN:
        print("[WARN] ไม่พบ LINE_CHANNEL_ACCESS_TOKEN — พิมพ์ข้อความแทนการส่งจริง:")
        print(text)
        return False

    chunks = _split_utf16(text)

    ok = True
    for chunk in chunks:
        if not _send_one(chunk):
            ok = False

    return ok
