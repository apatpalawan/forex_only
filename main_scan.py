"""
สแกนหาโอกาสเทรด: คู่เงิน/ทอง ที่ D1 มี price action ชัดเจนทั้งขาขึ้นและขาลง
และ H1 กำลังอยู่ในช่วง sideway (กำลังสร้างกรอบก่อน breakout)

แทนที่จะส่ง LINE ทันทีทุกครั้งที่เจอ - จะ "เก็บสะสม" คู่เงินที่เจอไว้ใน state.json ก่อน
แล้วรอจนถึงเวลาที่กำหนดใน config.SEND_TIMES ค่อยส่งสรุปทั้งหมดทีเดียว
จากนั้นล้างรายการที่เก็บไว้ทิ้ง เพื่อเริ่มสะสมรอบใหม่

แนะนำให้ตั้ง cron ของ workflow นี้ให้รันถี่ขึ้น (เช่น ทุก 15 นาที) เพื่อให้ "สะสม" มีความหมาย
ถ้ายังรันแค่ตรงเวลาส่งเป๊ะๆ เหมือนเดิม การสะสมจะไม่ต่างจากเดิมเพราะสแกน = ส่งเวลาเดียวกันเสมอ
"""

import datetime

import config
from data_fetcher import fetch_ohlc
from analysis import has_price_action_d1, detect_sideway_box
from state_manager import load_state, save_state
from line_notify import send_line_message


def _now_th():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=7)


def _matched_send_slot(now_th):
    """ถ้าเวลาตอนนี้ (เวลาไทย) ใกล้กับเวลาใน config.SEND_TIMES พอ (ภายใน tolerance)
    ให้คืนค่า slot string เช่น "2026-08-08 08:00" ไม่งั้นคืน None"""
    for t in config.SEND_TIMES:
        hh, mm = map(int, t.split(":"))
        target = now_th.replace(hour=hh, minute=mm, second=0, microsecond=0)
        diff_min = abs((now_th - target).total_seconds()) / 60
        if diff_min <= config.SEND_TIME_TOLERANCE_MIN:
            return f"{now_th.strftime('%Y-%m-%d')} {t}"
    return None


def run():
    state = load_state(config.STATE_FILE)
    pending = state.get(config.PENDING_KEY, {})

    found_this_run = []

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

            # เก็บสะสมไว้ใน pending รอเวลาส่ง (ถ้ามีอยู่แล้วให้อัปเดตกรอบล่าสุด)
            pending[name] = {
                "box_high": box_high,
                "box_low": box_low,
                "found_at": datetime.datetime.utcnow().isoformat(),
            }
            found_this_run.append(name)

        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            continue

    state[config.PENDING_KEY] = pending

    if found_this_run:
        print(f"[SCAN] เจอเข้าเงื่อนไขรอบนี้: {', '.join(found_this_run)} (เก็บสะสมไว้ก่อน)")
    else:
        print("[SCAN] รอบนี้ไม่พบคู่เงินที่เข้าเงื่อนไขใหม่")

    now_th = _now_th()
    slot = _matched_send_slot(now_th)
    already_sent = state.get(config.LAST_SENT_SLOT_KEY) == slot

    if slot and not already_sent:
        header = f"📊 รายงานสรุป {now_th.strftime('%d/%m/%Y %H:%M')} น.\n(D1 price action + H1 sideway)"
        if pending:
            lines = [
                f"• {name}: กรอบ {info['box_low']:.4f} - {info['box_high']:.4f}"
                for name, info in pending.items()
            ]
            msg = header + "\n" + "\n".join(lines) + "\n\nจะแจ้งเตือนทันทีเมื่อราคา breakout ออกจากกรอบ"
        else:
            msg = header + "\nช่วงที่ผ่านมาไม่พบคู่เงิน/ทองคำที่เข้าเงื่อนไข"

        sent_ok = send_line_message(msg)
        print(msg)

        if sent_ok:
            # ส่งสำเร็จแล้ว -> ล้างรายการที่เก็บไว้ทิ้ง เพื่อรอข้อมูลใหม่รอบถัดไป
            state[config.PENDING_KEY] = {}
            state[config.LAST_SENT_SLOT_KEY] = slot
        else:
            print("[WARN] ส่ง LINE ไม่สำเร็จ — คงรายการ pending ไว้ ลองส่งใหม่รอบหน้า")
    else:
        if slot and already_sent:
            print(f"[SKIP-SEND] ส่งรอบ {slot} ไปแล้ว รอ slot ถัดไป")
        else:
            print(f"[SKIP-SEND] ยังไม่ถึงเวลาส่ง (สะสมไว้ {len(pending)} คู่เงิน)")

    save_state(config.STATE_FILE, state)


if __name__ == "__main__":
    run()
