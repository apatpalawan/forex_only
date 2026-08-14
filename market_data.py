"""
market_data.py
Fetches D1 and H1 OHLC candles for a symbol via yfinance.

Uses a curl_cffi browser-impersonation session to reduce the chance of
Yahoo Finance rate-limiting/blocking requests coming from GitHub Actions'
shared IP ranges (this bit us on a previous bot, so it's built in here
from the start).
"""

import time
import random
import pandas as pd
import yfinance as yf

import config

try:
    from curl_cffi import requests as cffi_requests
    _SESSION = cffi_requests.Session(impersonate="chrome")
except Exception:
    # curl_cffi not available for some reason -> fall back to yfinance's default session
    _SESSION = None


def _fetch(ticker: str, period: str, interval: str) -> pd.DataFrame:
    last_err = None
    for attempt in range(1, config.FETCH_MAX_RETRIES + 1):
        try:
            kwargs = dict(period=period, interval=interval, auto_adjust=False)
            if _SESSION is not None:
                kwargs["session"] = _SESSION
            df = yf.Ticker(ticker).history(**kwargs)
            if df is None or df.empty:
                raise ValueError(f"empty dataframe for {ticker} ({interval})")
            df = df.dropna(subset=["Close"])
            return df
        except Exception as e:
            last_err = e
            # small jittered backoff before retrying
            time.sleep(config.FETCH_RETRY_DELAY_SEC + random.uniform(0, 1.5))
    raise RuntimeError(f"failed to fetch {ticker} ({interval}) after {config.FETCH_MAX_RETRIES} attempts: {last_err}")


def get_d1_candles(ticker: str) -> pd.DataFrame:
    """Daily candles. Caller is responsible for dropping the still-forming last bar."""
    return _fetch(ticker, config.D1_PERIOD, config.D1_INTERVAL)


def get_h1_candles(ticker: str) -> pd.DataFrame:
    """1-hour candles. Caller is responsible for dropping the still-forming last bar."""
    return _fetch(ticker, config.H1_PERIOD, config.H1_INTERVAL)
