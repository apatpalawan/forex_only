"""
ตรวจจับการเคลื่อนไหวราคาที่รุนแรงกระทันหันบน D1 แล้วแจ้งเตือนทันที
ไม่ต้องรอรอบเวลาปกติ (08:00 / 10:00 / 13:00 / 15:00 / 19:00)
แจ้งแค่ 1 ครั้งต่อวันต่อคู่เงิน (กันสแปม)
"""
import datetime

import config
from data_fetcher import fetch_ohlc
from analysis import detect_sudden_move_d1
from state_manager import load_state, save_state
from line_notify import send_line_message

DATE_KEY = "sudden_alerted_date"


def run():
    state = load_state(config.STATE_FILE)
    today_str = datetime.date.today().isoformat()

    for name, yf_symbol in config.FOREX_SYMBOLS.items():
        try:
            df_d1 = fetch_ohlc(yf_symbol, interval="1d", period="3mo")
            if df_d1 is None or len(df_d1) < 20:
                continue

            is_sudden, direction, today_range, atr = detect_sudden_move_d1(
                df_d1, move_threshold_atr=config.SUDDEN_MOVE_ATR_RATIO
            )

            key = f"{name}_sudden"
            already_alerted = state.get(key, {}).get(DATE_KEY) == today_str

            if is_sudden and not already_alerted:
                arrow = "🚀" if direction == "UP" else "💥"
                msg = (
                    f"{arrow} เคลื่อนไหวรุนแรงกระทันหันบน D1: {name}\n"
                    f"ทิศทาง: {'ขาขึ้น' if direction == 'UP' else 'ขาลง'}\n"
                    f"Range วันนี้: {today_range:.4f} (~{today_range / atr:.1f}x ATR)"
                )
                send_line_message(msg)
                print(msg)
                state[key] = {DATE_KEY: today_str}

        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            continue

    save_state(config.STATE_FILE, state)


if __name__ == "__main__":
    run()
