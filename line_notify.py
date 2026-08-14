"""
line_notify.py
Sends the radar result to LINE via the LINE Messaging API (push message).
"""

import requests
import config

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def format_message(scan_label: str, matches: list) -> str:
    """
    matches: list of dicts like
        {"symbol": "EURUSD", "direction": "BUY", "d1_cross": "CROSS UP", "h1_cross": "CROSS UP"}
    """
    lines = ["📊 FOREX MACD RADAR", "", f"⏰ Scan: {scan_label}", ""]

    if not matches:
        lines.append("ไม่มีคู่เงินที่ผ่านเงื่อนไขรอบนี้")
        return "\n".join(lines)

    for m in matches:
        emoji = "🟢" if m["direction"] == "BUY" else "🔴"
        lines.append(f"{emoji} {m['symbol']}")
        lines.append(f"D1 : MACD {m['d1_cross']}")
        lines.append(f"H1 : MACD {m['h1_cross']}")
        lines.append(f"Signal : {m['direction']} BIAS")
        lines.append("")

    return "\n".join(lines).rstrip()


def send_line_message(text: str) -> bool:
    """Returns True only on a real confirmed success from the LINE API."""
    if not config.LINE_CHANNEL_ACCESS_TOKEN or not config.LINE_TO:
        print("[line_notify] Missing LINE_CHANNEL_ACCESS_TOKEN or LINE_TO env var - skipping send.")
        return False

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": config.LINE_TO,
        "messages": [{"type": "text", "text": text}],
    }

    try:
        resp = requests.post(LINE_PUSH_URL, headers=headers, json=payload, timeout=15)
    except Exception as e:
        print(f"[line_notify] request failed: {e}")
        return False

    if resp.status_code == 200:
        print("[line_notify] sent OK")
        return True

    print(f"[line_notify] LINE API error {resp.status_code}: {resp.text}")
    return False
