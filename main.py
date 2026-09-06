"""
Pure M1 Bot
สัญญาณเดียว ต้องผ่านครบทุกเงื่อนไข (AND เข้มสุด): sideway breakout+volume,
EMA50x100 cross, EMA9x20 pullback confirmation, MACD, RSI, ADX+DI
ไปทิศทางเดียวกันทั้งหมด (ไม่สนใจ D1/H1/M15 อีกต่อไป)

รันไฟล์นี้เพื่อสแกนทุก symbol ใน config.SYMBOLS แล้วส่ง LINE เฉพาะเมื่อเจอสัญญาณจริงเท่านั้น
"""

import sys
import time
import config
from lib.data_fetcher import fetch_m1
from lib.strategy import evaluate_symbol
from lib.session_filter import in_trading_session
from lib.news_filter import is_blocked_by_news
from lib.state_manager import load_state, save_state, already_alerted, alerts_today, record_alert
from lib.line_notify import format_m1_alert, send_line_message

# หน่วงเวลาสั้น ๆ ระหว่าง symbol กันโดน Yahoo Finance rate-limit (สำคัญขึ้น
# มากตอนนี้ที่ลิสต์ symbol ขยายจาก 1 ตัว เป็น ~29 ตัว - ปัญหานี้เคยเจอมา
# แล้วจริงในบอทพี่น้องกัน apatpalawan/forex-radar-v8)
INTER_SYMBOL_DELAY_SEC = 0.5


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

            df_m1 = fetch_m1(symbol)
            time.sleep(INTER_SYMBOL_DELAY_SEC)

            signal = evaluate_symbol(symbol, df_m1)
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
