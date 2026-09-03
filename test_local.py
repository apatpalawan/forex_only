"""
Test local - ทดสอบ logic ของ Pure M1 Bot แบบ offline ล้วน ๆ (ไม่ต้องต่อ internet)
ใช้ข้อมูลสังเคราะห์ (synthetic OHLCV) แทนการดึงจาก yfinance จริง

วิธีรัน:
    python test_local.py
"""

import numpy as np
import pandas as pd

import config
from lib.indicators import ema, atr
from lib.strategy import (
    drop_unclosed_candle,
    _sideway_zone,
    _breakout_direction,
    _volume_momentum_ok,
    _ema_cross_direction,
    evaluate_symbol,
)

PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"[PASS] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name}")


def make_df(closes, opens=None, highs=None, lows=None, volumes=None):
    n = len(closes)
    opens = opens or closes
    highs = highs or [max(o, c) + 0.01 for o, c in zip(opens, closes)]
    lows = lows or [min(o, c) - 0.01 for o, c in zip(opens, closes)]
    volumes = volumes or [100] * n
    idx = pd.date_range("2026-01-01", periods=n, freq="1min")
    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": volumes},
        index=idx,
    )


# ==========================================================
# drop_unclosed_candle
# ==========================================================
df_5 = make_df([1, 2, 3, 4, 5])
check("drop_unclosed_candle ตัดแท่งสุดท้ายออก 1 แท่ง", len(drop_unclosed_candle(df_5)) == 4)
check("drop_unclosed_candle: df สั้นเกินไป (<=1 แท่ง) คืนค่าเดิม", len(drop_unclosed_candle(make_df([1]))) == 1)

# ==========================================================
# _sideway_zone
# ==========================================================
# กรอบแคบ 20 แท่ง (สลับ 99.9-100.1) -> ควรนับเป็น sideway
tight_closes = [100.0 + (0.1 if i % 2 == 0 else -0.1) for i in range(25)]
df_tight = make_df(tight_closes)
zone = _sideway_zone(df_tight)
check("_sideway_zone: กรอบแคบ -> เจอ zone", zone is not None)
if zone:
    check("_sideway_zone: high/low สมเหตุสมผล", zone["high"] > zone["low"])

# กรอบกว้าง: เทรนด์ลื่นไหลทางเดียว (ไม่ zigzag) ทำให้ range สะสมมาก
# แต่ ATR ต่อแท่ง (per-bar) ยังน้อย เพราะแต่ละแท่งขยับไม่กระโดด -
# ต่างจาก _sideway_zone: กรอบแคบ ด้านบนตรงที่นี่คือ "แนวโน้มทางเดียว
# ยาว ๆ" ไม่ใช่ "แกว่งไปมาในกรอบ" ถึงจะไม่ถือเป็น sideway จริง
wide_closes = list(np.linspace(100.0, 130.0, 25))
df_wide = make_df(wide_closes)
check("_sideway_zone: เทรนด์ทางเดียวยาว (ไม่ใช่กรอบ) -> None", _sideway_zone(df_wide) is None)

check(
    "_sideway_zone: ข้อมูลไม่พอ (< lookback+1 แท่ง) -> None",
    _sideway_zone(make_df([100.0] * 5)) is None,
)

# ==========================================================
# _breakout_direction
# ==========================================================
zone_fixed = {"high": 101.0, "low": 99.0}
df_break_up = make_df([100.0] * 24 + [101.5])
check("_breakout_direction: ทะลุขึ้น -> 'up'", _breakout_direction(df_break_up, zone_fixed) == "up")

df_break_down = make_df([100.0] * 24 + [98.5])
check("_breakout_direction: ทะลุลง -> 'down'", _breakout_direction(df_break_down, zone_fixed) == "down")

df_no_break = make_df([100.0] * 25)
check("_breakout_direction: ยังอยู่ในกรอบ -> None", _breakout_direction(df_no_break, zone_fixed) is None)

# ==========================================================
# _volume_momentum_ok
# ==========================================================
df_vol_spike = make_df([100.0] * 25, volumes=[100] * 24 + [300])  # 3 เท่าของ 100
check("_volume_momentum_ok: volume พุ่ง 3 เท่า -> True", _volume_momentum_ok(df_vol_spike) is True)

df_vol_normal = make_df([100.0] * 25, volumes=[100] * 25)
check("_volume_momentum_ok: volume ปกติ -> False", _volume_momentum_ok(df_vol_normal) is False)

df_vol_zero = make_df([100.0] * 25, volumes=[0] * 25)
check(
    "_volume_momentum_ok: symbol ไม่มี volume จริง (เช่น FX cross) -> False ไม่ crash",
    _volume_momentum_ok(df_vol_zero) is False,
)

# ==========================================================
# _ema_cross_direction (ใช้ config จริง: EMA50 x EMA100)
# ==========================================================
# ดาวน์เทรนด์ยาวพอให้ EMA50 < EMA100 แล้วจบด้วยแท่งขึ้นแรง ๆ
n = 150
downtrend = list(np.linspace(120, 100, n - 1))
df_cross_candidate = make_df(downtrend + [downtrend[-1] + 5])
cross = _ema_cross_direction(df_cross_candidate)
check(
    "_ema_cross_direction: ไม่ crash และคืนค่าที่ถูกต้อง (None/'up'/'down')",
    cross in (None, "up", "down"),
)

flat_df = make_df([100.0] * 150)
check("_ema_cross_direction: ราคานิ่งตลอด ไม่มีจุดตัด -> None", _ema_cross_direction(flat_df) is None)

# ==========================================================
# evaluate_symbol - เงื่อนไข AND: breakout+volume "และ" EMA cross
# ต้องเกิดพร้อมกันบนแท่งเดียวกัน ไปทิศทางเดียวกัน
#
# หมายเหตุ: การบังคับให้ EMA50/EMA100 (period ยาว) ตัดกันพอดีที่แท่ง
# สุดท้ายเป๊ะ ๆ ด้วยข้อมูลสังเคราะห์ทำได้ยาก (แท่งเดียวมีน้ำหนักต่อ EMA100
# น้อยมาก) จึงย่อ period ลงชั่วคราวเฉพาะในเทสต์นี้ (M1_EMA_FAST/SLOW)
# เพื่อทดสอบ "ตรรกะการรวมเงื่อนไข AND" ของ evaluate_symbol โดยตรง -
# ไม่ได้ทดสอบว่าค่า 50/100 ตัวจริงถูกต้อง (อันนั้นเทสต์แยกไว้ข้างบนแล้ว
# ด้วย _ema_cross_direction ที่ใช้ config จริง)
# ==========================================================
_orig_fast, _orig_slow = config.M1_EMA_FAST, config.M1_EMA_SLOW
config.M1_EMA_FAST, config.M1_EMA_SLOW = 10, 30

try:
    # สร้าง: ดาวน์เทรนด์สั้น ๆ (ให้ EMA10 < EMA30) + sideway แคบ 20 แท่ง
    # + แท่งสุดท้ายทะลุขึ้นแรงพร้อม volume พุ่ง -> ควรตัดขึ้นพอดีที่แท่งนี้
    lead_in = list(np.linspace(102, 100, 40))
    sideway = [100.0 + (0.01 if i % 2 == 0 else -0.01) for i in range(20)]
    closes_up = lead_in + sideway + [103.0]
    volumes_up = [100] * (len(closes_up) - 1) + [400]
    df_signal_up = make_df(closes_up + [103.0], volumes=volumes_up + [100])  # +1 แท่งยังไม่ปิดต่อท้าย

    sig_up = evaluate_symbol("TESTUP", df_signal_up)
    check("evaluate_symbol: ครบทั้ง breakout+volume+EMA cross ทิศเดียวกัน -> เจอสัญญาณ 'up'",
          sig_up is not None and sig_up["direction"] == "up")

    # กรณีเดียวกันแต่ไม่มี volume spike -> ต้องไม่มีสัญญาณ (AND ตก)
    df_no_volume = make_df(closes_up + [102.0])  # volume default เท่ากันหมด ไม่พุ่ง
    sig_no_vol = evaluate_symbol("TESTNOVOL", df_no_volume)
    check("evaluate_symbol: breakout+EMA cross แต่ volume ไม่พุ่ง -> ไม่มีสัญญาณ (AND ตก)",
          sig_no_vol is None)

    # กรณี breakout ขึ้น แต่ EMA10 อยู่เหนือ EMA30 อยู่แล้วตั้งแต่ก่อนเข้ากรอบ
    # sideway (lead-in เป็นขาขึ้นแทนขาลง) ทำให้แท่ง breakout ขึ้นแท่งสุดท้าย
    # ไม่ได้ทำให้เกิด "จุดตัดใหม่" (fast อยู่เหนือ slow อยู่แล้วมาตลอด) ->
    # ไม่ควรมีสัญญาณ
    up_lead_in = list(np.linspace(95, 100, 40))
    closes_break_only = up_lead_in + sideway + [102.0]
    volumes_break_only = [100] * (len(closes_break_only) - 1) + [400]
    df_break_only = make_df(closes_break_only + [102.0], volumes=volumes_break_only + [100])
    sig_break_only = evaluate_symbol("TESTBREAKONLY", df_break_only)
    check("evaluate_symbol: breakout+volume แต่ไม่มีจุดตัด EMA ใหม่ -> ไม่มีสัญญาณ (AND ตก)",
          sig_break_only is None)

    # ไม่มีอะไรเกิดขึ้นเลย (ราคานิ่งสนิท) -> None แน่นอน
    check("evaluate_symbol: ไม่มีสัญญาณอะไรเลย -> None",
          evaluate_symbol("TESTFLAT", make_df([100.0] * 155)) is None)

    # df ว่าง/None -> ไม่ crash
    check("evaluate_symbol: df None -> None ไม่ crash", evaluate_symbol("TESTNONE", None) is None)
    check("evaluate_symbol: df ว่างเปล่า -> None ไม่ crash",
          evaluate_symbol("TESTEMPTY", pd.DataFrame()) is None)

finally:
    config.M1_EMA_FAST, config.M1_EMA_SLOW = _orig_fast, _orig_slow


print()
print("=" * 40)
print(f"RESULT: PASS {PASS} / FAIL {FAIL}")
print("=" * 40)

if FAIL > 0:
    import sys
    sys.exit(1)
