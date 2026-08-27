"""
M1 Multi-Timeframe Trigger Bot
D1 (ทิศทาง) -> H1 (ความแข็งแรง: ADX/DI/ATR) -> M15 (โซน pullback+reversal) -> M1 (trigger ยืนยันแท่งปิด)

รันไฟล์นี้เพื่อสแกนทุก symbol ใน config.SYMBOLS แล้วส่ง LINE เฉพาะเมื่อเจอ trigger จริงเท่านั้น
"""

import sys
import config
from lib.data_fetcher import fetch_all_timeframes
from lib.strategy import evaluate_symbol
from lib.session_filter import in_trading_session
from lib.news_filter import is_blocked_by_news
from lib.state_manager import load_state, save_state, already_alerted, alerts_today, record_alert
from lib.line_notify import format_m1_alert, send_line_message


def run():
    if not in_trading_session():
        print("[main] outside trading session, skip scan")
        return

    state = load_state()
    sent_count = 0

    for symbol in config.SYMBOLS:
        try:
            if alerts_today(state, symbol) >= config.MAX_ALERTS_PER_SYMBOL_PER_DAY:
                continue

            candles = fetch_all_timeframes(symbol)
            signal = evaluate_symbol(symbol, candles)
            if signal is None:
                continue

            if already_alerted(state, symbol, signal["trigger_time"]):
                continue  # แจ้งเตือนแท่งนี้ไปแล้ว

            if is_blocked_by_news(symbol):
                print(f"[main] {symbol} signal found but blocked by news filter")
                continue

            text = format_m1_alert(signal)
            sent = send_line_message(text)
            if sent:
                record_alert(state, symbol, signal["trigger_time"])
                sent_count += 1
                print(f"[main] ALERT sent: {symbol} {signal['direction']} @ {signal['trigger_price']}")

        except Exception as e:
            print(f"[main] error evaluating {symbol}: {e}")

    save_state(state)
    print(f"[main] scan done, alerts sent: {sent_count}")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"[main] fatal error: {e}")
        sys.exit(1)
