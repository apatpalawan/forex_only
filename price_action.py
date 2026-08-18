"""
price_action.py
Detects a "sideway then breakout" pattern on H1 candles only:

1. Look at the SIDEWAY_LOOKBACK closed candles right before the candle being
   tested - if their high/low range is tight relative to recent volatility
   (ATR), that period counts as "sideway" (consolidation).
2. If the next closed candle's Close breaks above the sideway range's high
   (or below its low), that's a breakout.

Only the last CLOSED candle is ever tested (the still-forming candle is
always dropped first), so signals don't flicker before a candle finishes.
"""

import pandas as pd
import config


def _atr(df: pd.DataFrame, period: int) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period).mean()


def detect_sideway_breakout(df: pd.DataFrame):
    """
    Returns a dict:
        {"signal": "BREAKOUT_UP" | "BREAKOUT_DOWN" | None,
         "time": <Timestamp of the breakout candle, or None>,
         "range_high": float or None,
         "range_low": float or None}
    """
    empty = {"signal": None, "time": None, "range_high": None, "range_low": None}

    min_len = config.SIDEWAY_LOOKBACK + config.ATR_PERIOD + 2
    if df is None or len(df) < min_len:
        return empty

    closed = df.iloc[:-1]  # drop the still-forming candle
    if len(closed) < config.SIDEWAY_LOOKBACK + config.ATR_PERIOD + 1:
        return empty

    atr_series = _atr(closed, config.ATR_PERIOD)

    breakout_candle = closed.iloc[-1]
    # The sideway range is built from the N candles BEFORE the breakout
    # candle - the breakout candle itself is never part of its own range.
    window = closed.iloc[-(config.SIDEWAY_LOOKBACK + 1):-1]

    range_high = float(window["High"].max())
    range_low = float(window["Low"].min())
    range_width = range_high - range_low

    atr_value = atr_series.iloc[-2]  # ATR as of the last window candle
    if pd.isna(atr_value) or atr_value <= 0:
        return empty

    is_sideway = range_width <= (config.ATR_MULTIPLIER * atr_value)
    if not is_sideway:
        return {"signal": None, "time": None, "range_high": range_high, "range_low": range_low}

    close_price = float(breakout_candle["Close"])
    if close_price > range_high:
        return {"signal": "BREAKOUT_UP", "time": closed.index[-1], "range_high": range_high, "range_low": range_low}
    if close_price < range_low:
        return {"signal": "BREAKOUT_DOWN", "time": closed.index[-1], "range_high": range_high, "range_low": range_low}

    return {"signal": None, "time": None, "range_high": range_high, "range_low": range_low}
