"""
เช็คว่าราคาหลุดกรอบ sideway (H1) ที่บันทึกไว้จาก main_scan.py หรือยัง
ควรตั้ง cron ให้รันถี่ (แนะนำทุก 15 นาที) เพื่อจับสัญญาณ breakout ได้ใกล้เคียง real-time
แจ้งเตือนแค่ครั้งเดียวต่อกรอบ (ผ่าน flag "signaled" ใน state.json) กันแจ้งซ้ำรัว ๆ
"""
import config
from data_fetcher import fetch_ohlc
from analysis import check_breakout
from state_manager import load_state, save_state
from line_notify import send_line_message


def run():
    state = load_state(config.STATE_FILE)
    if not state:
        print("ยังไม่มีกรอบที่บันทึกไว้ รอรอบ main_scan ก่อน")
        return

    for name, box in state.items():
        if "box_high" not in box or box.get("signaled"):
            continue

        yf_symbol = config.FOREX_SYMBOLS.get(name)
        if not yf_symbol:
            continue

        try:
            df_h1 = fetch_ohlc(yf_symbol, interval="60m", period="5d")
            if df_h1 is None or df_h1.empty:
                continue

            latest_price = float(df_h1["Close"].iloc[-1])

            direction = check_breakout(
                latest_price,
                box["box_high"],
                box["box_low"],
                config.BREAKOUT_BUFFER_ATR,
                box["atr_h1"],
            )

            if direction:
                arrow = "🔼" if direction == "UP" else "🔽"
                msg = (
                    f"{arrow} BREAKOUT! {name}\n"
                    f"ราคาปัจจุบัน: {latest_price:.4f}\n"
                    f"กรอบเดิม: {box['box_low']:.4f} - {box['box_high']:.4f}\n"
                    f"ทิศทาง: {'ขาขึ้น' if direction == 'UP' else 'ขาลง'}"
                )
                send_line_message(msg)
                print(msg)
                state[name]["signaled"] = True

        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            continue

    save_state(config.STATE_FILE, state)


if __name__ == "__main__":
    run()
