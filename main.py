"""
สแกนทุก symbol ใน config.SYMBOLS บน timeframe M1
เงื่อนไข:
  ขาขึ้น: EMA100 ตัด EMA300 ขึ้นก่อนเสมอ -> EMA9 เรียงตัวเหนือ EMA25
          -> ยืนยันด้วย MACD (macd>signal), RSI(>50), ADX/DI (ADX>=min, +DI>-DI)
  ขาลง: ตรงข้ามทั้งหมด
แจ้งเตือนเข้า LINE เฉพาะตอนสัญญาณเปลี่ยน (กันสแปมทุก 5 นาทีที่ workflow รัน)
รันด้วยมือ (ไม่มี LINE_CHANNEL_ACCESS_TOKEN) จะ print ผลออก console แทนการส่งจริง
"""
import time

import config
from lib import data_fetcher, strategy, state_manager, line_notify


def format_message(display_symbol: str, signal: str, details: dict) -> str:
    icon = "🟢" if signal == "buy" else "🔴"
    action = "Buy" if signal == "buy" else "Sell"
    return (
        f"{icon} {action} {display_symbol} (M1)\n"
        f"EMA100/300: {details['trend']} | EMA9/25: {details['ema9']}/{details['ema25']}\n"
        f"RSI {details['rsi']} | ADX {details['adx']}"
    )


def run():
    state = state_manager.load_state(config.STATE_FILE)

    for display_symbol, ticker in config.SYMBOLS.items():
        df = data_fetcher.fetch_m1(ticker, config.INTERVAL, config.RANGE)

        if df.empty or len(df) < config.EMA_TREND_SLOW + 5:
            print(f"[{display_symbol}] skipped: not enough M1 data")
            time.sleep(config.SYMBOL_FETCH_DELAY_SEC)
            continue

        result = strategy.evaluate(df, config)
        signal = result["signal"]

        if state_manager.should_alert(state, display_symbol, signal):
            msg = format_message(display_symbol, signal, result["details"])
            line_notify.send_message(msg, config)
            print(f"[{display_symbol}] ALERT sent: {signal}")
        else:
            print(f"[{display_symbol}] signal={signal} reason={result['reason']} (no alert)")

        state_manager.update_state(state, display_symbol, signal)
        time.sleep(config.SYMBOL_FETCH_DELAY_SEC)

    state_manager.save_state(config.STATE_FILE, state)


if __name__ == "__main__":
    run()
