"""
macd_scanner.py
Computes MACD/Signal and detects a fresh cross on the LAST CLOSED candle only
(the currently-forming candle is always dropped before checking).

A "cross" means the relationship between MACD and Signal flipped between the
previous closed candle and the latest closed candle - NOT just "MACD is
currently above/below Signal" (that would re-trigger on every scan).
"""

import pandas as pd
import config


def _add_macd(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ema_fast = df["Close"].ewm(span=config.MACD_FAST, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=config.MACD_SLOW, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["Signal"] = df["MACD"].ewm(span=config.MACD_SIGNAL, adjust=False).mean()
    return df


def detect_cross(df: pd.DataFrame):
    """
    df: raw OHLC dataframe (may include a still-forming last candle).

    Returns a dict:
        {"cross": "UP" | "DOWN" | None, "time": <Timestamp of the closed
         candle where the cross happened, or None>}
    """
    if df is None or len(df) < config.MACD_SLOW + config.MACD_SIGNAL + 2:
        return {"cross": None, "time": None}

    # Drop the last row: it's the currently-forming (not-yet-closed) candle.
    closed = df.iloc[:-1]
    if len(closed) < 2:
        return {"cross": None, "time": None}

    closed = _add_macd(closed)

    prev = closed.iloc[-2]
    latest = closed.iloc[-1]

    prev_diff = prev["MACD"] - prev["Signal"]
    latest_diff = latest["MACD"] - latest["Signal"]

    if prev_diff <= 0 and latest_diff > 0:
        return {"cross": "UP", "time": closed.index[-1]}
    if prev_diff >= 0 and latest_diff < 0:
        return {"cross": "DOWN", "time": closed.index[-1]}

    return {"cross": None, "time": None}
