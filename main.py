"""
main.py
Forex + Gold MACD Radar Bot

Flow (per run):
    D1 MACD cross scan
        -> keep symbols with a fresh D1 cross (temporary, in-memory only)
    H1 MACD cross scan (only for symbols that passed D1)
        -> keep symbols where H1 crossed the SAME direction as D1,
           and the H1 cross happened AFTER the D1 cross
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
    """Returns a match dict if this symbol passes D1 -> H1, else None."""
    try:
        d1_df = market_data.get_d1_candles(ticker)
    except Exception as e:
        print(f"[{display_name}] D1 fetch failed: {e}")
        return None

    d1_result = macd_scanner.detect_cross(d1_df)
    if d1_result["cross"] is None:
        return None  # step 1: no fresh D1 cross -> reject

    print(f"[{display_name}] D1 {d1_result['cross']} at {d1_result['time']}")

    try:
        h1_df = market_data.get_h1_candles(ticker)
    except Exception as e:
        print(f"[{display_name}] H1 fetch failed: {e}")
        return None

    h1_result = macd_scanner.detect_cross(h1_df)
    if h1_result["cross"] is None:
        return None  # step 2: no fresh H1 cross -> reject

    if h1_result["cross"] != d1_result["cross"]:
        return None  # different direction -> reject

    # H1 cross must occur AFTER the D1 cross
    d1_time = d1_result["time"]
    h1_time = h1_result["time"]
    try:
        if d1_time.tzinfo is not None and h1_time.tzinfo is None:
            h1_time = h1_time.tz_localize(d1_time.tzinfo)
        elif h1_time.tzinfo is not None and d1_time.tzinfo is None:
            d1_time = d1_time.tz_localize(h1_time.tzinfo)
        if h1_time <= d1_time:
            print(f"[{display_name}] H1 cross ({h1_time}) not after D1 cross ({d1_time}) -> reject")
            return None
    except Exception:
        pass  # if timestamps aren't comparable for some reason, don't hard-fail the whole scan

    direction = "BUY" if d1_result["cross"] == "UP" else "SELL"
    return {
        "symbol": display_name,
        "direction": direction,
        "d1_cross": "CROSS UP" if d1_result["cross"] == "UP" else "CROSS DOWN",
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
