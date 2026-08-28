"""
Strategy - D1 (ทิศทาง) -> H1 (ความแข็งแรง) -> M15 (โซน pullback + reversal) -> M1 (trigger ยืนยันแท่งปิด)

M1 ไม่มี indicator เพิ่มเติมของตัวเอง - ใช้แค่ยืนยันว่าแท่ง M1 "ปิด" ทะลุ high/low
ของแท่งกลับตัวที่เจอบน M15 ตามหลักการที่ตกลงกันไว้ (กัน noise/repaint จาก timeframe เล็ก)

ทุก timeframe (D1/H1/M15/M1) ตัดแท่งสุดท้ายที่ "ยังไม่ปิด" ออกก่อนคำนวณ indicator เสมอ
(yfinance คืนแท่งปัจจุบันที่กำลังก่อตัวมาด้วย ถ้าไม่ตัดออก ค่า EMA/MACD/ADX จะ repaint
ได้ก่อนแท่งนั้นปิดจริง) - ดู drop_unclosed_candle()
"""

import pandas as pd
import config
from lib.indicators import ema, macd, atr, adx_di


def drop_unclosed_candle(df: pd.DataFrame) -> pd.DataFrame:
    """ตัดแท่งสุดท้ายออก (ถือว่ายังไม่ปิด/กำลังก่อตัว) เหลือเฉพาะแท่งที่ปิดแล้วจริง"""
    if df is None or len(df) <= 1:
        return df
    return df.iloc[:-1]


def d1_direction(df_d1: pd.DataFrame) -> str | None:
    """คืน 'up' / 'down' / None (ไม่มีทิศทางชัด)"""
    close = df_d1["Close"]
    ema_fast = ema(close, config.EMA_FAST)
    ema_slow = ema(close, config.EMA_SLOW)
    macd_line, signal_line, _ = macd(close, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL)

    ema_up = ema_fast.iloc[-1] > ema_slow.iloc[-1]
    macd_up = macd_line.iloc[-1] > signal_line.iloc[-1]

    if ema_up and macd_up:
        return "up"
    if (not ema_up) and (not macd_up):
        return "down"
    return None  # D1 ยังไม่ชัด (EMA กับ MACD ขัดกัน) - ข้ามคู่นี้ไปก่อน


def h1_strength_ok(df_h1: pd.DataFrame, direction: str) -> tuple[bool, dict]:
    """เช็คว่า H1 ยืนยันความแข็งแรงของเทรนด์ทิศทางที่ D1 บอกไว้หรือไม่ คืน (ผ่านไหม, ค่าที่ใช้เช็ค เผื่อ debug/log)"""
    adx_series, plus_di, minus_di = adx_di(df_h1, config.ADX_PERIOD)
    atr_series = atr(df_h1, config.ATR_PERIOD)

    adx_now = adx_series.iloc[-1]
    adx_prev = adx_series.iloc[-2]
    di_plus_now = plus_di.iloc[-1]
    di_minus_now = minus_di.iloc[-1]
    atr_now = atr_series.iloc[-1]
    atr_avg = atr_series.tail(config.ATR_LOOKBACK_AVG).mean()

    info = {
        "adx": round(float(adx_now), 2),
        "adx_prev": round(float(adx_prev), 2),
        "di_plus": round(float(di_plus_now), 2),
        "di_minus": round(float(di_minus_now), 2),
        "atr_ratio": round(float(atr_now / atr_avg), 2) if atr_avg else None,
    }

    if pd.isna(adx_now) or pd.isna(di_plus_now) or pd.isna(di_minus_now) or not atr_avg:
        return False, info

    if adx_now <= config.ADX_MIN:
        return False, info
    if config.ADX_MUST_RISE and adx_now <= adx_prev:
        return False, info
    if abs(di_plus_now - di_minus_now) < config.DI_GAP_MIN:
        return False, info
    if (atr_now / atr_avg) < config.ATR_RATIO_MIN:
        return False, info

    if direction == "up" and di_plus_now <= di_minus_now:
        return False, info
    if direction == "down" and di_minus_now <= di_plus_now:
        return False, info

    return True, info


def find_m15_reversal_zone(df_m15: pd.DataFrame, direction: str):
    """
    หาแท่ง M15 ล่าสุดที่: ราคาย่อเข้าใกล้ EMA20(M15) แล้วเกิดแท่งกลับตัวตามทิศทาง D1/H1
    คืน dict {"time", "high", "low"} ของแท่งกลับตัวนั้น หรือ None ถ้าไม่เจอ
    """
    close = df_m15["Close"]
    ema20 = ema(close, config.EMA_FAST)
    tail = df_m15.tail(config.M15_LOOKBACK_BARS)
    ema_tail = ema20.tail(config.M15_LOOKBACK_BARS)

    for i in range(len(tail) - 1, 0, -1):  # จากแท่งล่าสุดย้อนกลับไป
        row = tail.iloc[i]
        e20 = ema_tail.iloc[i]
        if pd.isna(e20) or e20 == 0:
            continue

        dist_pct = abs(row["Close"] - e20) / e20 * 100
        if dist_pct > config.PULLBACK_EMA_TOLERANCE_PCT:
            continue  # แท่งนี้ไม่ได้อยู่ใกล้ EMA20 พอ

        prev_row = tail.iloc[i - 1]
        is_bull_reversal = row["Close"] > row["Open"] and prev_row["Close"] < prev_row["Open"]
        is_bear_reversal = row["Close"] < row["Open"] and prev_row["Close"] > prev_row["Open"]

        if direction == "up" and is_bull_reversal:
            return {"time": tail.index[i], "high": float(row["High"]), "low": float(row["Low"])}
        if direction == "down" and is_bear_reversal:
            return {"time": tail.index[i], "high": float(row["High"]), "low": float(row["Low"])}

    return None


def m1_trigger(df_m1: pd.DataFrame, direction: str, zone: dict):
    """
    เช็คว่ามีแท่ง M1 'ปิด' ทะลุ high (ถ้า up) หรือ low (ถ้า down) ของโซน M15 หรือไม่
    ภายใน M1_CONFIRM_WINDOW_BARS แท่งหลังโซนก่อตัว
    คืน (แท่ง trigger หรือ None, เวลาแท่งนั้น)
    """
    m1_after_zone = df_m1[df_m1.index > zone["time"]]
    if m1_after_zone.empty:
        return None

    window = m1_after_zone.head(config.M1_CONFIRM_WINDOW_BARS)
    # ใช้เฉพาะแท่งที่ "ปิดแล้ว" เท่านั้น (ตัดแท่งสุดท้ายที่อาจยังไม่ปิดออกถ้าจำเป็นในฝั่ง main.py)
    for ts, row in window.iterrows():
        if direction == "up" and row["Close"] > zone["high"]:
            return {"time": ts, "close": float(row["Close"])}
        if direction == "down" and row["Close"] < zone["low"]:
            return {"time": ts, "close": float(row["Close"])}

    return None


def m1_range_spike(df_m1: pd.DataFrame) -> bool:
    """เช็คว่าแท่ง M1 ล่าสุดกว้างผิดปกติไหม (proxy กันช่วง spike ข่าว/สภาพคล่องต่ำ) - True = ให้ข้าม"""
    atr_m1 = atr(df_m1, period=14)
    last_range = df_m1["High"].iloc[-1] - df_m1["Low"].iloc[-1]
    avg_atr = atr_m1.tail(30).mean()
    if not avg_atr or pd.isna(avg_atr):
        return False
    return (last_range / avg_atr) > config.SKIP_IF_M1_RANGE_RATIO_ABOVE


def evaluate_symbol(symbol: str, candles: dict):
    """
    ประเมินสัญลักษณ์เดียวผ่านทุกชั้น (D1->H1->M15->M1)
    คืน dict สัญญาณถ้าเจอ trigger จริง มิฉะนั้นคืน None
    """
    df_d1, df_h1, df_m15, df_m1 = candles.get("D1"), candles.get("H1"), candles.get("M15"), candles.get("M1")
    if any(df is None for df in (df_d1, df_h1, df_m15, df_m1)):
        return None

    # ตัดแท่งสุดท้ายที่ยังไม่ปิดออกทุก timeframe ก่อนคำนวณอะไรทั้งสิ้น (กัน repaint)
    df_d1 = drop_unclosed_candle(df_d1)
    df_h1 = drop_unclosed_candle(df_h1)
    df_m15 = drop_unclosed_candle(df_m15)
    df_m1_closed = drop_unclosed_candle(df_m1)
    if any(df is None or df.empty for df in (df_d1, df_h1, df_m15, df_m1_closed)):
        return None

    direction = d1_direction(df_d1)
    if direction is None:
        return None

    h1_ok, h1_info = h1_strength_ok(df_h1, direction)
    if not h1_ok:
        return None

    zone = find_m15_reversal_zone(df_m15, direction)
    if zone is None:
        return None

    if m1_range_spike(df_m1_closed):
        return None  # แท่ง M1 ล่าสุดกว้างผิดปกติ - ข้าม กันสัญญาณหลอกช่วง spike

    trigger = m1_trigger(df_m1_closed, direction, zone)
    if trigger is None:
        return None

    return {
        "symbol": symbol,
        "direction": direction,
        "h1_info": h1_info,
        "zone_time": str(zone["time"]),
        "trigger_time": str(trigger["time"]),
        "trigger_price": trigger["close"],
    }
