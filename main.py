"""
main.py
Forex + Gold H1 Sideway-Breakout Radar Bot

Flow (per run):
    For each symbol:
        - fetch H1 candles
        - check if the SIDEWAY_LOOKBACK closed candles before the latest
          closed candle were "sideway" (tight range vs ATR)
        - check if the latest closed candle broke out of that range
    Only alert for a breakout candle that hasn't been alerted before
    (tracked in state.json, committed back to the repo after each run -
    prevents the same breakout being sent twice while the H1 candle is
    still the "latest closed" one across two 30-min scans in the same hour)
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import config
import market_data
import price_action
import line_notify
import state_manager

TH_TZ = ZoneInfo("Asia/Bangkok")


def scan_symbol(display_name: str, ticker: str, state: dict):
    try:
        h1_df = market_data.get_h1_candles(ticker)
    except Exception as e:
        print(f"[{display_name}] H1 fetch failed: {e}")
        return None

    result = price_action.detect_sideway_breakout(h1_df)
    if result["signal"] is None:
        return None

    candle_time = str(result["time"])
    if state.get(display_name) == candle_time:
        print(f"[{display_name}] {result['signal']} at {candle_time} already alerted - skip")
        return None

    print(f"[{display_name}] {result['signal']} at {candle_time}")
    state[display_name] = candle_time  # mark this candle as alerted

    direction = "BUY" if result["signal"] == "BREAKOUT_UP" else "SELL"
    return {
        "symbol": display_name,
        "direction": direction,
        "breakout": "BREAKOUT UP" if result["signal"] == "BREAKOUT_UP" else "BREAKOUT DOWN",
        "range_high": result["range_high"],
        "range_low": result["range_low"],
    }


def run():
    now_th = datetime.now(TH_TZ)
    scan_label = now_th.strftime("%H:%M")
    print(f"=== FOREX SIDEWAY-BREAKOUT RADAR - scan {scan_label} TH ({now_th.isoformat()}) ===")

    state = state_manager.load_state()

    matches = []
    for display_name, ticker in config.SYMBOLS.items():
        result = scan_symbol(display_name, ticker, state)
        if result:
            matches.append(result)

    print(f"Matches this round: {[m['symbol'] + ' ' + m['direction'] for m in matches]}")

    if matches:
        message = line_notify.format_message(scan_label, matches)
        line_notify.send_line_message(message)
    else:
        print("No matches this round - not sending a LINE message.")

    state_manager.save_state(state)


if __name__ == "__main__":
    run()
