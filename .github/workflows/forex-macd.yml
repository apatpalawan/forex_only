"""
main.py
Forex + Gold MACD Radar Bot (H1-only)

Flow (per run):
    H1 MACD cross scan for every symbol
        -> any symbol with a fresh H1 cross (on the last CLOSED H1 candle)
           is kept as a match, no other confirmation needed
    Send one LINE message with all matches
    Exit (nothing is persisted -> next scheduled run starts completely fresh)
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import config
import market_data
import macd_scanner
import line_notify

TH_TZ = ZoneInfo("Asia/Bangkok")


def scan_symbol(display_name: str, ticker: str):
    """H1-only: returns a match dict if H1 has a fresh MACD cross, else None."""
    try:
        h1_df = market_data.get_h1_candles(ticker)
    except Exception as e:
        print(f"[{display_name}] H1 fetch failed: {e}")
        return None

    h1_result = macd_scanner.detect_cross(h1_df)
    if h1_result["cross"] is None:
        return None  # no fresh H1 cross -> reject

    print(f"[{display_name}] H1 {h1_result['cross']} at {h1_result['time']}")

    direction = "BUY" if h1_result["cross"] == "UP" else "SELL"
    return {
        "symbol": display_name,
        "direction": direction,
        "h1_cross": "CROSS UP" if h1_result["cross"] == "UP" else "CROSS DOWN",
    }


def run():
    now_th = datetime.now(TH_TZ)
    scan_label = now_th.strftime("%H:%M")
    print(f"=== FOREX MACD RADAR - scan {scan_label} TH ({now_th.isoformat()}) ===")

    matches = []  # in-memory only for this run -> nothing persists between runs
    for display_name, ticker in config.SYMBOLS.items():
        result = scan_symbol(display_name, ticker)
        if result:
            matches.append(result)

    print(f"Matches this round: {[m['symbol'] + ' ' + m['direction'] for m in matches]}")

    message = line_notify.format_message(scan_label, matches)

    if matches:
        line_notify.send_line_message(message)
    else:
        print("No matches this round - not sending a LINE message.")
        # If you'd rather always get a heartbeat message even with 0 matches,
        # uncomment the next line:
        # line_notify.send_line_message(message)


if __name__ == "__main__":
    run()