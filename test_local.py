"""
Test local - ทดสอบ logic ของ Pure M1 Bot แบบ offline ล้วน ๆ (ไม่ต้องต่อ internet)
ใช้ข้อมูลสังเคราะห์ (synthetic OHLCV) แทนการดึงจาก yfinance จริง

แนวทางทดสอบ:
1. ทดสอบแต่ละ indicator/helper function แยกด้วยข้อมูลจริงที่คำนวณตรง ๆ
   (rsi, macd confirm, adx confirm, sideway/breakout, ema cross ค้นย้อนหลัง)
2. ทดสอบ evaluate_symbol() ที่เป็นตัวรวมเงื่อนไข AND ทั้ง 6 ข้อ โดยสลับ
   helper function ภายในเป็นค่าจำลอง (monkeypatch) แทนการพยายามสร้างราคา
   สังเคราะห์ให้ MACD/RSI/ADX/EMA ทั้งหมดตรงกันพอดีเป๊ะ ๆ พร้อมกัน ซึ่งเปราะ
   บางเกินไปสำหรับเทสต์ - วิธีนี้ยืนยันได้ตรง ๆ ว่า "ตรรกะ AND" ต่อ/ตัดถูกต้อง
   โดยไม่ขึ้นกับความบังเอิญของข้อมูลสังเคราะห์

วิธีรัน:
    python test_local.py
"""

import numpy as np
import pandas as pd

import config
import lib.strategy as strategy
from lib.indicators import rsi
from lib.strategy import (
    drop_unclosed_candle,
    _sideway_zone_ending_at,
    _breakout_direction_at,
    find_recent_breakout,
    _ema_cross_direction_at,
    find_recent_ema_cross,
    _macd_confirms,
    _rsi_confirms,
    _adx_confirms,
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
# rsi()
# ==========================================================
uptrend = pd.Series(np.linspace(100, 150, 60))
downtrend = pd.Series(np.linspace(150, 100, 60))
flat = pd.Series([100.0] * 60)

check("rsi: ขาขึ้นล้วน -> RSI สูง (>70)", rsi(uptrend, 14).iloc[-1] > 70)
check("rsi: ขาลงล้วน -> RSI ต่ำ (<30)", rsi(downtrend, 14).iloc[-1] < 30)
check("rsi: ราคานิ่ง -> RSI ~50 (ไม่ crash แม้ avg_loss=0)", abs(rsi(flat, 14).iloc[-1] - 50) < 1)

# ==========================================================
# _sideway_zone_ending_at / _breakout_direction_at
# ==========================================================
tight_closes = [100.0 + (0.1 if i % 2 == 0 else -0.1) for i in range(25)]
df_tight = make_df(tight_closes)
zone = _sideway_zone_ending_at(df_tight, 20)  # ใช้แท่ง 0-19 หา zone
check("_sideway_zone_ending_at: กรอบแคบ -> เจอ zone", zone is not None)

trend_closes = list(np.linspace(100.0, 130.0, 25))
df_trend = make_df(trend_closes)
check("_sideway_zone_ending_at: เทรนด์ทางเดียวยาว (ไม่ใช่กรอบ) -> None",
      _sideway_zone_ending_at(df_trend, 20) is None)

check("_sideway_zone_ending_at: ข้อมูลไม่พอ -> None", _sideway_zone_ending_at(make_df([100.0] * 5), 20) is None)

zone_fixed = {"high": 101.0, "low": 99.0}
df_break_up = make_df([100.0] * 24 + [101.5])
check("_breakout_direction_at: ทะลุขึ้น -> 'up'", _breakout_direction_at(df_break_up, 24, zone_fixed) == "up")

df_break_down = make_df([100.0] * 24 + [98.5])
check("_breakout_direction_at: ทะลุลง -> 'down'", _breakout_direction_at(df_break_down, 24, zone_fixed) == "down")

df_no_break = make_df([100.0] * 25)
check("_breakout_direction_at: ยังอยู่ในกรอบ -> None", _breakout_direction_at(df_no_break, 24, zone_fixed) is None)

# find_recent_breakout: breakout เกิดที่แท่งกลาง ๆ ของกรอบค้นหา ต้องเจอย้อนหลังได้
# (ไม่เช็ค volume แล้ว - ใช้ MACD/RSI/ADX ยืนยันโมเมนตัมแทนในเลเยอร์อื่น)
closes_with_breakout_mid = [100.0] * 20 + [100.0 + (0.05 if i % 2 == 0 else -0.05) for i in range(20)] + [102.0] + [102.0] * 9
df_recent_breakout = make_df(closes_with_breakout_mid)
found_pos = find_recent_breakout(df_recent_breakout, "up", upto_pos=len(df_recent_breakout) - 1, lookback_bars=15)
check("find_recent_breakout: เจอ breakout ย้อนหลังในกรอบเวลาได้", found_pos == 40)

check("find_recent_breakout: ค้นในกรอบที่ไม่ครอบคลุม breakout -> None",
      find_recent_breakout(df_recent_breakout, "up", upto_pos=len(df_recent_breakout) - 1, lookback_bars=5) is None)

# ==========================================================
# _ema_cross_direction_at / find_recent_ema_cross
# ==========================================================
n = 150
downtrend_long = list(np.linspace(102, 100, 40)) + [100.0 + (0.01 if i % 2 == 0 else -0.01) for i in range(20)] + [103.0]
df_cross = make_df(downtrend_long)
pos_last = len(df_cross) - 1
cross_at_last = _ema_cross_direction_at(df_cross, 10, 30, pos_last)
check("_ema_cross_direction_at: จุดตัดที่ตำแหน่งท้ายสุด -> 'up'", cross_at_last == "up")
check("_ema_cross_direction_at: ตำแหน่งก่อนหน้า ยังไม่ตัด -> None",
      _ema_cross_direction_at(df_cross, 10, 30, pos_last - 5) is None)

found = find_recent_ema_cross(df_cross, 10, 30, "up", upto_pos=pos_last, lookback_bars=10)
check("find_recent_ema_cross: ค้นย้อนหลังเจอจุดตัดที่ถูกต้อง", found == pos_last)
check("find_recent_ema_cross: ทิศทางผิด -> None",
      find_recent_ema_cross(df_cross, 10, 30, "down", upto_pos=pos_last, lookback_bars=10) is None)

# ==========================================================
# _macd_confirms / _rsi_confirms / _adx_confirms (ใช้ config จริง)
# ==========================================================
strong_up = make_df(list(np.linspace(100, 160, 120)))
strong_down = make_df(list(np.linspace(160, 100, 120)))
pos_up = len(strong_up) - 1
pos_down = len(strong_down) - 1

check("_macd_confirms: เทรนด์ขึ้นแรง -> True สำหรับ 'up'", _macd_confirms(strong_up, pos_up, "up") is True)
check("_macd_confirms: เทรนด์ขึ้นแรง -> False สำหรับ 'down'", _macd_confirms(strong_up, pos_up, "down") is False)
check("_rsi_confirms: เทรนด์ขึ้นแรง -> True สำหรับ 'up'", _rsi_confirms(strong_up, pos_up, "up") is True)
check("_rsi_confirms: เทรนด์ลงแรง -> True สำหรับ 'down'", _rsi_confirms(strong_down, pos_down, "down") is True)
check("_adx_confirms: เทรนด์ขึ้นแรงต่อเนื่อง -> True สำหรับ 'up'", _adx_confirms(strong_up, pos_up, "up") is True)
check("_adx_confirms: เทรนด์ขึ้นแรง แต่เช็คทิศ 'down' -> False", _adx_confirms(strong_up, pos_up, "down") is False)

flat_df_150 = make_df([100.0] * 150)
pos_flat = len(flat_df_150) - 1
check("_adx_confirms: ราคานิ่งสนิท (ไม่มี trend) -> False", _adx_confirms(flat_df_150, pos_flat, "up") is False)

# ==========================================================
# evaluate_symbol - ตรรกะ AND ทั้ง 6 เงื่อนไข (monkeypatch helper แต่ละตัว
# เพื่อทดสอบการต่อ/ตัดของ evaluate_symbol โดยตรง ไม่ขึ้นกับข้อมูลสังเคราะห์)
# ==========================================================
_dummy_df = make_df([100.0] * (config.M1_EMA_SLOW + config.M1_PULLBACK_LOOKBACK_BARS + 10))

# เก็บของจริงไว้ก่อน แล้วค่อย restore ท้ายสุด
_orig = {
    "_ema_cross_direction_at": strategy._ema_cross_direction_at,
    "find_recent_ema_cross": strategy.find_recent_ema_cross,
    "find_recent_breakout": strategy.find_recent_breakout,
    "_macd_confirms": strategy._macd_confirms,
    "_rsi_confirms": strategy._rsi_confirms,
    "_adx_confirms": strategy._adx_confirms,
}


def patch_all(trigger_dir="up", main_ema_found=True, breakout_found=True,
              macd_ok=True, rsi_ok=True, adx_ok=True):
    strategy._ema_cross_direction_at = lambda df, f, s, pos: trigger_dir
    strategy.find_recent_ema_cross = lambda df, f, s, d, upto_pos, lookback_bars: (0 if main_ema_found else None)
    strategy.find_recent_breakout = lambda df, d, upto_pos, lookback_bars: (0 if breakout_found else None)
    strategy._macd_confirms = lambda df, pos, d: macd_ok
    strategy._rsi_confirms = lambda df, pos, d: rsi_ok
    strategy._adx_confirms = lambda df, pos, d: adx_ok


def restore_all():
    for name, fn in _orig.items():
        setattr(strategy, name, fn)


try:
    # ทุกเงื่อนไขผ่านหมด -> ต้องได้สัญญาณ
    patch_all()
    sig = strategy.evaluate_symbol("TESTALL", _dummy_df)
    check("evaluate_symbol: ผ่านครบทุกเงื่อนไข -> ได้สัญญาณ 'up'", sig is not None and sig["direction"] == "up")

    # ไม่มี EMA9x20 cross เลย (trigger เอง None) -> ไม่มีสัญญาณ
    patch_all()
    strategy._ema_cross_direction_at = lambda df, f, s, pos: None
    check("evaluate_symbol: ไม่มี EMA9x20 cross (trigger) -> None", strategy.evaluate_symbol("T", _dummy_df) is None)

    # ไม่มี EMA50x100 cross ก่อนหน้า (ไม่ผ่าน pullback confirmation) -> ไม่มีสัญญาณ
    patch_all(main_ema_found=False)
    check("evaluate_symbol: ไม่มี EMA50x100 cross ย้อนหลัง -> None (AND ตก)",
          strategy.evaluate_symbol("T", _dummy_df) is None)

    # ไม่มี breakout ย้อนหลัง -> ไม่มีสัญญาณ
    patch_all(breakout_found=False)
    check("evaluate_symbol: ไม่มี breakout ย้อนหลัง -> None (AND ตก)",
          strategy.evaluate_symbol("T", _dummy_df) is None)

    # MACD ไม่ยืนยัน -> ไม่มีสัญญาณ
    patch_all(macd_ok=False)
    check("evaluate_symbol: MACD ไม่ยืนยัน -> None (AND ตก)", strategy.evaluate_symbol("T", _dummy_df) is None)

    # RSI ไม่ยืนยัน -> ไม่มีสัญญาณ
    patch_all(rsi_ok=False)
    check("evaluate_symbol: RSI ไม่ยืนยัน -> None (AND ตก)", strategy.evaluate_symbol("T", _dummy_df) is None)

    # ADX ไม่ยืนยัน (trend ไม่แรงพอ หรือทิศไม่ตรง) -> ไม่มีสัญญาณ
    patch_all(adx_ok=False)
    check("evaluate_symbol: ADX ไม่ยืนยัน -> None (AND ตก)", strategy.evaluate_symbol("T", _dummy_df) is None)

    # ขาลงก็ต้องทำงานเหมือนกัน (symmetry)
    patch_all(trigger_dir="down")
    sig_down = strategy.evaluate_symbol("TESTDOWN", _dummy_df)
    check("evaluate_symbol: ผ่านครบทุกเงื่อนไข ขาลง -> ได้สัญญาณ 'down'",
          sig_down is not None and sig_down["direction"] == "down")

    # df ว่าง/สั้นเกินไป -> ไม่ crash
    check("evaluate_symbol: df None -> None ไม่ crash", strategy.evaluate_symbol("T", None) is None)
    check("evaluate_symbol: df สั้นเกินไป -> None ไม่ crash", strategy.evaluate_symbol("T", make_df([100.0] * 10)) is None)

finally:
    restore_all()


print()
print("=" * 40)
print(f"RESULT: PASS {PASS} / FAIL {FAIL}")
print("=" * 40)

if FAIL > 0:
    import sys
    sys.exit(1)
