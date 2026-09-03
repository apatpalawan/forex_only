"""
Strategy - Pure M1 เท่านั้น ไม่สนใจ D1/H1/M15 อีกต่อไป

สัญญาณเดียว: ต้องเกิด "sideway breakout + volume momentum" พร้อมกันกับ
"EMA50 ตัด EMA100" บนแท่ง M1 ที่ปิดล่าสุดแท่งเดียวกัน และไปทิศทางเดียวกัน
(AND ไม่ใช่ OR ตามที่ตกลงกันไว้) ทำทั้งขาขึ้น (BUY) และขาลง (SELL)

ตัดแท่งสุดท้ายที่ "ยังไม่ปิด" ออกก่อนคำนวณ indicator เสมอ (yfinance คืน
แท่งปัจจุบันที่กำลังก่อตัวมาด้วย ถ้าไม่ตัดออก ค่า EMA/ATR จะ repaint ได้
ก่อนแท่งนั้นปิดจริง)
"""

import pandas as pd
import config
from lib.indicators import ema, atr


def drop_unclosed_candle(df: pd.DataFrame) -> pd.DataFrame:
    """ตัดแท่งสุดท้ายออก (ถือว่ายังไม่ปิด/กำลังก่อตัว) เหลือเฉพาะแท่งที่ปิดแล้วจริง"""
    if df is None or len(df) <= 1:
        return df
    return df.iloc[:-1]


def _sideway_zone(df: pd.DataFrame):
    """
    ใช้ M1_SIDEWAY_LOOKBACK แท่งก่อนแท่งล่าสุด หา high/low ของกรอบ
    แล้วเช็คว่ากรอบแคบพอ (เทียบ ATR) ถึงจะถือว่าเป็น sideway จริง
    คืน {"high", "low"} หรือ None ถ้าไม่ใช่ sideway
    """
    lookback = config.M1_SIDEWAY_LOOKBACK
    if len(df) < lookback + 1:
        return None

    window = df.iloc[-(lookback + 1):-1]  # ไม่รวมแท่งล่าสุด (แท่งที่กำลังเช็ค breakout)
    zone_high = float(window["High"].max())
    zone_low = float(window["Low"].min())
    zone_range = zone_high - zone_low

    atr_series = atr(df, config.M1_ATR_PERIOD)
    atr_now = atr_series.iloc[-2]  # ATR ของแท่งสุดท้ายในกรอบ (ก่อนแท่ง breakout)
    if pd.isna(atr_now) or atr_now <= 0:
        return None

    if (zone_range / atr_now) > config.M1_SIDEWAY_MAX_RANGE_ATR_RATIO:
        return None  # กรอบกว้างเกินไป ไม่ใช่ sideway จริง

    return {"high": zone_high, "low": zone_low}


def _breakout_direction(df: pd.DataFrame, zone: dict):
    """เช็คแท่งล่าสุด (ปิดแล้ว) ว่าทะลุกรอบ sideway ทางไหน คืน 'up' / 'down' / None"""
    last = df.iloc[-1]
    close = float(last["Close"])
    buf = config.M1_BREAKOUT_BUFFER_PCT / 100

    if close > zone["high"] * (1 + buf):
        return "up"
    if close < zone["low"] * (1 - buf):
        return "down"
    return None


def _volume_momentum_ok(df: pd.DataFrame) -> bool:
    """แท่งล่าสุด Volume >= M1_VOLUME_RATIO_MIN เท่าของค่าเฉลี่ย M1_VOLUME_LOOKBACK แท่งก่อนหน้า"""
    lookback = config.M1_VOLUME_LOOKBACK
    if len(df) < lookback + 1:
        return False

    last_volume = float(df["Volume"].iloc[-1])
    avg_volume = float(df["Volume"].iloc[-(lookback + 1):-1].mean())

    if avg_volume <= 0:
        return False  # กัน symbol ที่ไม่มีข้อมูล Volume จริงใช้งานได้ (เช่น FX cross สังเคราะห์)

    return (last_volume / avg_volume) >= config.M1_VOLUME_RATIO_MIN


def _ema_cross_direction(df: pd.DataFrame):
    """เช็คว่าแท่งล่าสุด (ปิดแล้ว) เป็นแท่งที่ EMA50 ตัด EMA100 หรือไม่ คืน 'up' / 'down' / None"""
    close = df["Close"]
    ema_fast = ema(close, config.M1_EMA_FAST)
    ema_slow = ema(close, config.M1_EMA_SLOW)

    if len(ema_fast) < 2 or pd.isna(ema_fast.iloc[-2]) or pd.isna(ema_slow.iloc[-2]):
        return None

    prev_fast, prev_slow = ema_fast.iloc[-2], ema_slow.iloc[-2]
    now_fast, now_slow = ema_fast.iloc[-1], ema_slow.iloc[-1]

    if prev_fast <= prev_slow and now_fast > now_slow:
        return "up"
    if prev_fast >= prev_slow and now_fast < now_slow:
        return "down"
    return None


def evaluate_symbol(symbol: str, df_m1: pd.DataFrame):
    """
    ประเมิน M1 เดี่ยว ๆ ของ symbol เดียว ต้องเกิดทั้งสองเงื่อนไขพร้อมกัน
    บนแท่งล่าสุดเดียวกัน และไปทิศทางเดียวกัน ถึงจะคืนสัญญาณ ไม่งั้นคืน None
    """
    if df_m1 is None or df_m1.empty:
        return None

    df = drop_unclosed_candle(df_m1)

    min_needed = max(config.M1_EMA_SLOW, config.M1_SIDEWAY_LOOKBACK, config.M1_VOLUME_LOOKBACK) + 2
    if df is None or df.empty or len(df) < min_needed:
        return None

    zone = _sideway_zone(df)
    if zone is None:
        return None

    breakout_dir = _breakout_direction(df, zone)
    if breakout_dir is None:
        return None

    if not _volume_momentum_ok(df):
        return None

    cross_dir = _ema_cross_direction(df)
    if cross_dir is None:
        return None

    if breakout_dir != cross_dir:
        return None  # สองเงื่อนไขต้องไปทิศทางเดียวกันด้วย ไม่งั้นไม่ถือว่า "เกิดพร้อมกัน" จริง

    last = df.iloc[-1]
    return {
        "symbol": symbol,
        "direction": breakout_dir,
        "trigger_time": str(df.index[-1]),
        "trigger_price": float(last["Close"]),
        "zone_high": zone["high"],
        "zone_low": zone["low"],
        "volume": float(last["Volume"]),
    }
