"""
Strategy - Pure M1 เท่านั้น ไม่สนใจ D1/H1/M15 อีกต่อไป

สัญญาณเดียว ต้องผ่านทุกเงื่อนไขพร้อมกันหมด (AND เข้มสุดตามที่ตกลงกันไว้)
ไปทิศทางเดียวกันทั้งหมด ทำทั้งขาขึ้น (BUY) และขาลง (SELL):

1. Sideway breakout                    (เกิดขึ้นภายใน M1_PULLBACK_LOOKBACK_BARS แท่งล่าสุด)
2. EMA50 ตัด EMA100                    (ยืนยัน trend ใหญ่ เกิดขึ้นภายในกรอบเวลาเดียวกัน)
3. EMA9 ตัด EMA20                      (จุดตัดบนแท่งล่าสุดพอดี = trigger จริง, ต้องเกิด "หลัง"
                                         จุดตัด EMA50x100 = pullback confirmation)
4. MACD                                (เส้น MACD อยู่เหนือ/ใต้ Signal ตรงทิศทาง)
5. RSI                                 (RSI > 50 = ขึ้น, RSI < 50 = ลง)
6. ADX + DI                            (ADX >= เกณฑ์ = trend แรงพอ, DI+/DI- ยืนยันทิศทาง)

หมายเหตุ: ไม่ใช้ Volume เป็นเงื่อนไขแล้ว (คู่เงิน Forex ส่วนใหญ่บน Yahoo
Finance ไม่มีข้อมูล Volume จริง เป็นตลาด OTC) ใช้ MACD/RSI/ADX ยืนยัน
โมเมนตัมแทนทั้งหมด

ใช้หลักการเดียวกันหมดกับทุก symbol ในลิสต์ (รวมทองคำ GC=F ด้วย - ไม่มี
การแยก logic พิเศษให้ symbol ใดเป็นการเฉพาะ)

ตัดแท่งสุดท้ายที่ "ยังไม่ปิด" ออกก่อนคำนวณ indicator เสมอ (yfinance คืน
แท่งปัจจุบันที่กำลังก่อตัวมาด้วย ถ้าไม่ตัดออก ค่า EMA/MACD/RSI/ADX จะ
repaint ได้ก่อนแท่งนั้นปิดจริง)
"""

import pandas as pd
import config
from lib.indicators import ema, atr, macd, rsi, adx_di


def drop_unclosed_candle(df: pd.DataFrame) -> pd.DataFrame:
    """ตัดแท่งสุดท้ายออก (ถือว่ายังไม่ปิด/กำลังก่อตัว) เหลือเฉพาะแท่งที่ปิดแล้วจริง"""
    if df is None or len(df) <= 1:
        return df
    return df.iloc[:-1]


# ==========================================================
# Sideway zone + Breakout (ใช้ index อ้างอิงแบบยืดหยุ่น เพื่อให้ค้นหา
# ย้อนหลังในกรอบเวลาได้ ไม่ใช่เช็คแค่แท่งล่าสุดแท่งเดียวเหมือนเดิม)
# ==========================================================

def _sideway_zone_ending_at(df: pd.DataFrame, end_pos: int):
    """
    หา high/low ของกรอบ sideway จาก M1_SIDEWAY_LOOKBACK แท่ง ที่ "จบก่อน"
    ตำแหน่ง end_pos (ไม่รวม end_pos เอง) แล้วเช็คว่าแคบพอ (เทียบ ATR)
    คืน {"high", "low"} หรือ None ถ้าไม่ใช่ sideway / ข้อมูลไม่พอ
    """
    lookback = config.M1_SIDEWAY_LOOKBACK
    start = end_pos - lookback
    if start < 0 or end_pos >= len(df) or end_pos < 1:
        return None

    window = df.iloc[start:end_pos]
    zone_high = float(window["High"].max())
    zone_low = float(window["Low"].min())
    zone_range = zone_high - zone_low

    atr_series = atr(df, config.M1_ATR_PERIOD)
    atr_at = atr_series.iloc[end_pos - 1]
    if pd.isna(atr_at) or atr_at <= 0:
        return None

    if (zone_range / atr_at) > config.M1_SIDEWAY_MAX_RANGE_ATR_RATIO:
        return None  # กรอบกว้างเกินไป ไม่ใช่ sideway จริง

    return {"high": zone_high, "low": zone_low}


def _breakout_direction_at(df: pd.DataFrame, pos: int, zone: dict):
    """เช็คแท่งที่ตำแหน่ง pos ว่าทะลุกรอบ sideway ทางไหน คืน 'up' / 'down' / None"""
    close = float(df["Close"].iloc[pos])
    buf = config.M1_BREAKOUT_BUFFER_PCT / 100

    if close > zone["high"] * (1 + buf):
        return "up"
    if close < zone["low"] * (1 - buf):
        return "down"
    return None


def find_recent_breakout(df: pd.DataFrame, direction: str, upto_pos: int, lookback_bars: int):
    """
    ค้นหาย้อนหลังจากตำแหน่ง upto_pos (รวม upto_pos) ถอยไปไม่เกิน lookback_bars
    แท่ง ว่ามีแท่งไหนเป็น breakout ไปทิศทาง direction บ้าง (ไม่เช็ค volume
    แล้ว - ใช้ MACD/RSI/ADX ยืนยันโมเมนตัมแทนที่ด้านล่าง)
    คืน position ของแท่งที่เจอ (ล่าสุดที่เจอ) หรือ None ถ้าไม่เจอเลย
    """
    earliest = max(0, upto_pos - lookback_bars + 1)
    for pos in range(upto_pos, earliest - 1, -1):
        zone = _sideway_zone_ending_at(df, pos)
        if zone is None:
            continue
        d = _breakout_direction_at(df, pos, zone)
        if d != direction:
            continue
        return pos
    return None


# ==========================================================
# EMA cross (ใช้ตำแหน่งยืดหยุ่นเหมือนกัน - ต้องหาได้ทั้งที่แท่งล่าสุด
# (EMA9x20 trigger) และค้นย้อนหลังในกรอบเวลา (EMA50x100 confirmation)
# ==========================================================

def _ema_cross_direction_at(df: pd.DataFrame, fast_period: int, slow_period: int, pos: int):
    """เช็คว่าแท่งที่ตำแหน่ง pos เป็นแท่งที่ EMA fast ตัด EMA slow หรือไม่ คืน 'up' / 'down' / None"""
    if pos < 1:
        return None

    close = df["Close"]
    ema_fast = ema(close, fast_period)
    ema_slow = ema(close, slow_period)

    prev_fast, prev_slow = ema_fast.iloc[pos - 1], ema_slow.iloc[pos - 1]
    now_fast, now_slow = ema_fast.iloc[pos], ema_slow.iloc[pos]

    if pd.isna(prev_fast) or pd.isna(prev_slow) or pd.isna(now_fast) or pd.isna(now_slow):
        return None

    if prev_fast <= prev_slow and now_fast > now_slow:
        return "up"
    if prev_fast >= prev_slow and now_fast < now_slow:
        return "down"
    return None


def find_recent_ema_cross(df: pd.DataFrame, fast_period: int, slow_period: int,
                           direction: str, upto_pos: int, lookback_bars: int):
    """ค้นหาย้อนหลังจาก upto_pos ถอยไปไม่เกิน lookback_bars แท่ง หาแท่งที่ EMA ตัดไปทิศทาง direction"""
    earliest = max(1, upto_pos - lookback_bars + 1)
    for pos in range(upto_pos, earliest - 1, -1):
        d = _ema_cross_direction_at(df, fast_period, slow_period, pos)
        if d == direction:
            return pos
    return None


# ==========================================================
# MACD / RSI / ADX confirmation (เช็คที่แท่ง trigger เท่านั้น - เป็นตัว
# กรองสถานะโมเมนตัม/ความแรงเทรนด์ ณ จุดที่จะยิงสัญญาณ ไม่ใช่ trigger เอง)
# ==========================================================

def _macd_confirms(df: pd.DataFrame, pos: int, direction: str) -> bool:
    close = df["Close"]
    macd_line, signal_line, _ = macd(
        close, config.M1_MACD_FAST, config.M1_MACD_SLOW, config.M1_MACD_SIGNAL
    )
    m, s = macd_line.iloc[pos], signal_line.iloc[pos]
    if pd.isna(m) or pd.isna(s):
        return False
    return bool((m > s) if direction == "up" else (m < s))


def _rsi_confirms(df: pd.DataFrame, pos: int, direction: str) -> bool:
    r = rsi(df["Close"], config.M1_RSI_PERIOD).iloc[pos]
    if pd.isna(r):
        return False
    if direction == "up":
        return bool(r > config.M1_RSI_BULL_THRESHOLD)
    return bool(r < config.M1_RSI_BEAR_THRESHOLD)


def _adx_confirms(df: pd.DataFrame, pos: int, direction: str) -> bool:
    adx_series, plus_di, minus_di = adx_di(df, config.M1_ADX_PERIOD)
    a, p, m = adx_series.iloc[pos], plus_di.iloc[pos], minus_di.iloc[pos]
    if pd.isna(a) or pd.isna(p) or pd.isna(m):
        return False
    if a < config.M1_ADX_MIN:
        return False  # trend ไม่แรงพอ ไม่ว่าจะทิศไหน
    return bool((p > m) if direction == "up" else (m > p))


# ==========================================================
# MAIN EVALUATION
# ==========================================================

def evaluate_symbol(symbol: str, df_m1: pd.DataFrame):
    """
    ประเมิน M1 เดี่ยว ๆ ต้องผ่านครบทุกเงื่อนไข (AND เข้มสุด) ถึงจะคืนสัญญาณ:

      trigger  = แท่งล่าสุดที่ปิดแล้ว เป็นแท่งที่ EMA9 ตัด EMA20 (ทิศทาง D)
      +        = ภายใน M1_PULLBACK_LOOKBACK_BARS แท่งก่อนหน้า (นับถึง trigger)
                 เคยมี EMA50 ตัด EMA100 ไปทิศทาง D มาก่อนแล้ว (pullback
                 confirmation - EMA9x20 ต้องตัด "หลัง" EMA50x100)
      +        = ภายในกรอบเวลาเดียวกัน เคยมี sideway breakout ไปทิศทาง D
                 มาก่อนแล้วเช่นกัน (ไม่เช็ค volume แล้ว)
      +        = ที่แท่ง trigger: MACD, RSI, ADX+DI ยืนยันทิศทาง D ทั้งหมด

    ไม่ผ่านข้อใดข้อหนึ่ง -> คืน None ใช้หลักการเดียวกันหมดกับทุก symbol
    """
    if df_m1 is None or df_m1.empty:
        return None

    df = drop_unclosed_candle(df_m1)

    min_needed = (
        max(config.M1_EMA_SLOW, config.M1_SIDEWAY_LOOKBACK)
        + config.M1_PULLBACK_LOOKBACK_BARS
        + 5
    )
    if df is None or df.empty or len(df) < min_needed:
        return None

    trigger_pos = len(df) - 1

    # 1) trigger จริง: EMA9 ตัด EMA20 บนแท่งล่าสุด
    direction = _ema_cross_direction_at(
        df, config.M1_EMA_PULLBACK_FAST, config.M1_EMA_PULLBACK_SLOW, trigger_pos
    )
    if direction is None:
        return None

    # 2) EMA50 ตัด EMA100 ไปทิศทางเดียวกัน ต้องเกิด "ก่อน" trigger ภายในกรอบเวลา
    #    (pullback confirmation: EMA9x20 คือแท่งล่าสุด จึงหาย้อนตั้งแต่แท่งก่อนแท่ง trigger)
    ema_main_pos = find_recent_ema_cross(
        df, config.M1_EMA_FAST, config.M1_EMA_SLOW, direction,
        upto_pos=trigger_pos - 1, lookback_bars=config.M1_PULLBACK_LOOKBACK_BARS,
    )
    if ema_main_pos is None:
        return None

    # 3) Sideway breakout ไปทิศทางเดียวกัน ภายในกรอบเวลาเดียวกัน
    breakout_pos = find_recent_breakout(
        df, direction, upto_pos=trigger_pos, lookback_bars=config.M1_PULLBACK_LOOKBACK_BARS,
    )
    if breakout_pos is None:
        return None

    # 4) MACD / 5) RSI / 6) ADX+DI - เช็คที่แท่ง trigger เท่านั้น ต้องผ่านทุกตัว
    if not _macd_confirms(df, trigger_pos, direction):
        return None
    if not _rsi_confirms(df, trigger_pos, direction):
        return None
    if not _adx_confirms(df, trigger_pos, direction):
        return None

    last = df.iloc[trigger_pos]
    return {
        "symbol": symbol,
        "direction": direction,
        "trigger_time": str(df.index[trigger_pos]),
        "trigger_price": float(last["Close"]),
        "ema_main_cross_time": str(df.index[ema_main_pos]),
        "breakout_time": str(df.index[breakout_pos]),
    }
