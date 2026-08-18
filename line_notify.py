"""
line_notify.py
Sends the sideway-breakout radar result to LINE via the LINE Messaging API.
"""

import requests
import config

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def format_message(scan_label: str, matches: list) -> str:
    """
    matches: list of dicts like
        {"symbol": "EURUSD", "direction": "BUY", "breakout": "BREAKOUT UP",
         "range_high": 1.0950, "range_low": 1.0910}
    """
    lines = ["📊 FOREX SIDEWAY-BREAKOUT RADAR", "", f"⏰ Scan: {scan_label}", ""]

    if not matches:
        lines.append("ไม่มีคู่เงินที่ผ่านเงื่อนไขรอบนี้")
        return "\n".join(lines)

    for m in matches:
        emoji = "🟢" if m["direction"] == "BUY" else "🔴"
        lines.append(f"{emoji} {m['symbol']}")
        lines.append(f"H1 : {m['breakout']}")
        lines.append(f"Range : {m['range_low']:.5f} - {m['range_high']:.5f}")
        lines.append(f"Signal : {m['direction']} BIAS")
        lines.append("")

    return "\n".join(lines).rstrip()


def send_line_message(text: str) -> bool:
    """Returns True only on a real confirmed success from the LINE API."""
    if not config.LINE_CHANNEL_ACCESS_TOKEN or not config.LINE_TARGET_IDS:
        print("[line_notify] Missing LINE_CHANNEL_ACCESS_TOKEN or LINE_TARGET_IDS env var - skipping send.")
        return False

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
    }

    target_ids = [t.strip() for t in config.LINE_TARGET_IDS.split(",") if t.strip()]
    all_ok = True
    for target_id in target_ids:
        payload = {
            "to": target_id,
            "messages": [{"type": "text", "text": text}],
        }
        try:
            resp = requests.post(LINE_PUSH_URL, headers=headers, json=payload, timeout=15)
        except Exception as e:
            print(f"[line_notify] request failed for {target_id}: {e}")
            all_ok = False
            continue

        if resp.status_code == 200:
            print(f"[line_notify] sent OK to {target_id}")
        else:
            print(f"[line_notify] LINE API error {resp.status_code} for {target_id}: {resp.text}")
            all_ok = False

    return all_ok
