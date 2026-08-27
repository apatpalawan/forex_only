"""
Data fetcher - ดึงราคาแท่งเทียนหลาย timeframe จาก yfinance
ใช้ curl_cffi impersonation + jitter delay ตามที่เคยแก้ปัญหาโดน Yahoo rate-limit บน GitHub Actions IP มาก่อน
"""

import time
import random
import pandas as pd
import yfinance as yf

try:
    from curl_cffi import requests as cffi_requests
    _SESSION = cffi_requests.Session(impersonate="chrome")
except Exception:
    _SESSION = None  # fallback เฉย ๆ ถ้าไม่มี curl_cffi ติดตั้ง

# yfinance interval / period ที่รองรับสำหรับแต่ละ timeframe ที่เราต้องใช้
_TF_MAP = {
    "D1":  {"interval": "1d",  "period": "1y"},
    "H1":  {"interval": "1h",  "period": "60d"},   # yfinance จำกัด intraday <1d ย้อนหลังได้ราว 60-730 วันแล้วแต่ interval
    "M15": {"interval": "15m", "period": "5d"},
    "M1":  {"interval": "1m",  "period": "5d"},    # yfinance จำกัด M1 ย้อนหลังได้แค่ ~7 วัน
}

MAX_RETRIES = 3
BASE_DELAY = 1.0


def fetch_candles(symbol: str, timeframe: str) -> pd.DataFrame | None:
    """คืน DataFrame (Open/High/Low/Close/Volume, index เป็นเวลา) หรือ None ถ้าดึงไม่สำเร็จ"""
    if timeframe not in _TF_MAP:
        raise ValueError(f"unknown timeframe: {timeframe}")

    cfg = _TF_MAP[timeframe]
    last_err = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ticker = yf.Ticker(symbol, session=_SESSION) if _SESSION else yf.Ticker(symbol)
            df = ticker.history(period=cfg["period"], interval=cfg["interval"])
            if df is None or df.empty:
                raise RuntimeError("empty dataframe")
            df = df.dropna(subset=["Close"])
            if len(df) < 5:
                raise RuntimeError(f"too few candles ({len(df)})")
            return df
        except Exception as e:
            last_err = e
            # jitter delay กันโดน rate-limit ซ้ำ
            time.sleep(BASE_DELAY * attempt + random.uniform(0, 0.5))

    print(f"[data_fetcher] FAILED {symbol} {timeframe}: {last_err}")
    return None


def fetch_all_timeframes(symbol: str) -> dict:
    """คืน dict {"D1": df, "H1": df, "M15": df, "M1": df} - ค่าที่ดึงไม่ได้จะเป็น None"""
    out = {}
    for tf in ("D1", "H1", "M15", "M1"):
        out[tf] = fetch_candles(symbol, tf)
        time.sleep(random.uniform(0.3, 0.8))  # jitter ระหว่าง symbol/timeframe
    return out
