"""
สแกนหาโอกาสเทรด: คู่เงิน/ทอง ที่ D1 มี price action ชัดเจนทั้งขาขึ้นและขาลง
และ H1 กำลังอยู่ในช่วง sideway (กำลังสร้างกรอบก่อน breakout)

รันตามเวลาที่กำหนด (08:00, 10:00, 13:00, 15:00, 19:00 น. เวลาไทย) ผ่าน GitHub Actions
บันทึกกรอบ (box) ของแต่ละคู่เงินไว้ใน state.json ให้ breakout_monitor.py เอาไปเช็คต่อ
"""
import datetime

import config
from data_fetcher import fetch_ohlc
from analysis import has_price_action_d1, detect_sideway_box
from state_manager import load_state, save_state
from line_notify import send_line_message


def run():
    state = load_state(config.STATE_FILE)
    lines = []

    for name, yf_symbol in config.FOREX_SYMBOLS.items():
        try:
            df_d1 = fetch_ohlc(yf_symbol, interval="1d", period="6mo")
            df_h1 = fetch_ohlc(yf_symbol, interval="60m", period="60d")

            if df_d1 is None or df_h1 is None or len(df_d1) < 30 or len(df_h1) < 30:
                print(f"[SKIP] {name}: ข้อมูลไม่พอ")
                continue

            has_pa, pa_info = has_price_action_d1(
                df_d1,
                config.D1_LOOKBACK,
                config.D1_MIN_ATR_PCT,
                config.D1_SWING_MIN_RATIO,
            )
            if not has_pa:
                continue

            is_side, box_high, box_low, atr_h1 = detect_sideway_box(
                df_h1, config.H1_LOOKBACK, config.H1_MAX_RANGE_ATR_RATIO
            )
            if not is_side:
                continue

            prev = state.get(name, {})
            # ถ้ากรอบใหม่ต่างจากกรอบเดิมมาก ถือว่าเป็นกรอบใหม่ -> reset สถานะแจ้งเตือน breakout
            box_changed = (
                prev.get("box_high") is None
                or abs(prev.get("box_high", 0) - box_high) > 0.1 * atr_h1
                or abs(prev.get("box_low", 0) - box_low) > 0.1 * atr_h1
            )

            state[name] = {
                "box_high": box_high,
                "box_low": box_low,
                "atr_h1": atr_h1,
                "signaled": False if box_changed else prev.get("signaled", False),
                "updated_at": datetime.datetime.utcnow().isoformat(),
            }

            lines.append(f"• {name}: กรอบ {box_low:.4f} - {box_high:.4f}")

        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            continue

    save_state(config.STATE_FILE, state)

    now_th = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    header = f"📊 รายงานสแกน {now_th.strftime('%d/%m/%Y %H:%M')} น.\n(D1 price action + H1 sideway)"

    if lines:
        msg = header + "\n" + "\n".join(lines) + "\n\nจะแจ้งเตือนทันทีเมื่อราคา breakout ออกจากกรอบ"
    else:
        msg = header + "\nรอบนี้ไม่พบคู่เงิน/ทองคำที่เข้าเงื่อนไข"

    send_line_message(msg)
    print(msg)


if __name__ == "__main__":
    run()
