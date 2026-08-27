"""
Indicators - EMA / MACD / ADX+DI / ATR
คำนวณด้วย pandas ล้วน ไม่พึ่ง TA-Lib (กันปัญหาติดตั้งบน CI)
"""

import pandas as pd
import numpy as np


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def macd(close: pd.Series, fast=12, slow=26, signal=9):
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def adx_di(df: pd.DataFrame, period: int = 14):
    """คืน (ADX, DI+, DI-) เป็น pd.Series ทั้งสามตัว"""
    high, low, close = df["High"], df["Low"], df["Close"]

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = atr(df, period=1) * 1.0  # true range ราย candle (period=1 = ไม่ smooth)
    atr_smooth = tr.ewm(alpha=1 / period, adjust=False).mean()

    plus_dm_smooth = pd.Series(plus_dm, index=df.index).ewm(alpha=1 / period, adjust=False).mean()
    minus_dm_smooth = pd.Series(minus_dm, index=df.index).ewm(alpha=1 / period, adjust=False).mean()

    plus_di = 100 * (plus_dm_smooth / atr_smooth.replace(0, np.nan))
    minus_di = 100 * (minus_dm_smooth / atr_smooth.replace(0, np.nan))

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()

    return adx, plus_di, minus_di
