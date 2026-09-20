"""
กลยุทธ์ M1:
  ขาขึ้น: EMA100 ตัด EMA300 ขึ้น (เกิดก่อนเสมอ, ใช้เป็นตัวกำหนดเทรนด์หลัก)
          จากนั้น EMA9 ต้องเรียงตัวอยู่เหนือ EMA25 (เช็คสถานะปัจจุบัน)
          ยืนยันด้วย MACD (macd line > signal line), RSI (>50), ADX/DI (ADX>=min และ +DI>-DI)
  ขาลง: ตรงข้ามทั้งหมด

evaluate() คืนค่า dict: {"signal": "buy"/"sell"/None, "reason": str, "details": {...}}
"""
import numpy as np
import pandas as pd

from lib import indicators as ind


def _trend_direction(ema_fast: pd.Series, ema_slow: pd.Series, lookback: int):
    """
    หาทิศทางเทรนด์จากจุดตัด EMA fast/slow ล่าสุดในช่วง lookback แท่งที่ผ่านมา
    (นับจากแท่งสุดท้าย ณ ปัจจุบันย้อนหลังไป)
    คืนค่า ('up'/'down'/None, cross_index หรือ None)
    ถ้าหาจุดตัดไม่เจอในช่วง lookback จะ fallback ไปใช้ความสัมพันธ์ปัจจุบันของ fast vs slow แทน
    """
    diff = ema_fast - ema_slow
    n = len(diff)
    if n < 2:
        return None, None

    start = max(1, n - lookback)
    for i in range(n - 1, start - 1, -1):
        prev = diff.iloc[i - 1]
        curr = diff.iloc[i]
        if pd.isna(prev) or pd.isna(curr):
            continue
        if prev <= 0 and curr > 0:
            return "up", i
        if prev >= 0 and curr < 0:
            return "down", i

    # ไม่เจอจุดตัดในช่วง lookback -> ใช้ความสัมพันธ์ปัจจุบันแทน (เทรนด์เป็นมานานแล้ว)
    last = diff.iloc[-1]
    if pd.isna(last):
        return None, None
    if last > 0:
        return "up", None
    if last < 0:
        return "down", None
    return None, None


def evaluate(df: pd.DataFrame, config) -> dict:
    """
    df: DataFrame ที่มีคอลัมน์ Open, High, Low, Close (แท่งสุดท้ายต้องเป็นแท่งที่ปิดแล้ว)
    config: module หรือ object ที่มี EMA_TREND_FAST, EMA_TREND_SLOW, TREND_CROSS_LOOKBACK_BARS,
            EMA_SIGNAL_FAST, EMA_SIGNAL_SLOW, MACD_FAST/SLOW/SIGNAL, RSI_PERIOD, RSI_MID,
            ADX_PERIOD, ADX_MIN
    """
    close = df["Close"]

    ema_trend_fast = ind.ema(close, config.EMA_TREND_FAST)
    ema_trend_slow = ind.ema(close, config.EMA_TREND_SLOW)
    ema_sig_fast = ind.ema(close, config.EMA_SIGNAL_FAST)
    ema_sig_slow = ind.ema(close, config.EMA_SIGNAL_SLOW)

    macd_line, macd_signal, _ = ind.macd(
        close, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL
    )
    rsi = ind.rsi(close, config.RSI_PERIOD)
    adx, plus_di, minus_di = ind.adx_di(df, config.ADX_PERIOD)

    required = [
        ema_trend_fast, ema_trend_slow, ema_sig_fast, ema_sig_slow,
        macd_line, macd_signal, rsi, adx, plus_di, minus_di,
    ]
    if any(pd.isna(s.iloc[-1]) for s in required):
        return {"signal": None, "reason": "not_enough_data", "details": {}}

    trend, cross_idx = _trend_direction(
        ema_trend_fast, ema_trend_slow, config.TREND_CROSS_LOOKBACK_BARS
    )

    details = {
        "trend": trend,
        "ema9": round(float(ema_sig_fast.iloc[-1]), 6),
        "ema25": round(float(ema_sig_slow.iloc[-1]), 6),
        "ema100": round(float(ema_trend_fast.iloc[-1]), 6),
        "ema300": round(float(ema_trend_slow.iloc[-1]), 6),
        "macd": round(float(macd_line.iloc[-1]), 6),
        "macd_signal": round(float(macd_signal.iloc[-1]), 6),
        "rsi": round(float(rsi.iloc[-1]), 2),
        "adx": round(float(adx.iloc[-1]), 2),
        "plus_di": round(float(plus_di.iloc[-1]), 2),
        "minus_di": round(float(minus_di.iloc[-1]), 2),
    }

    if trend is None:
        return {"signal": None, "reason": "no_trend", "details": details}

    ema9 = ema_sig_fast.iloc[-1]
    ema25 = ema_sig_slow.iloc[-1]
    macd_v = macd_line.iloc[-1]
    macd_s = macd_signal.iloc[-1]
    rsi_v = rsi.iloc[-1]
    adx_v = adx.iloc[-1]
    pdi = plus_di.iloc[-1]
    mdi = minus_di.iloc[-1]

    strong_enough = adx_v >= config.ADX_MIN

    if trend == "up":
        aligned = ema9 > ema25
        macd_ok = macd_v > macd_s
        rsi_ok = rsi_v > config.RSI_MID
        di_ok = pdi > mdi
        if aligned and macd_ok and rsi_ok and di_ok and strong_enough:
            return {"signal": "buy", "reason": "ok", "details": details}
        return {"signal": None, "reason": "conditions_not_met_up", "details": details}

    if trend == "down":
        aligned = ema9 < ema25
        macd_ok = macd_v < macd_s
        rsi_ok = rsi_v < config.RSI_MID
        di_ok = mdi > pdi
        if aligned and macd_ok and rsi_ok and di_ok and strong_enough:
            return {"signal": "sell", "reason": "ok", "details": details}
        return {"signal": None, "reason": "conditions_not_met_down", "details": details}

    return {"signal": None, "reason": "no_trend", "details": details}
