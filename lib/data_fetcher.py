"""
Data fetcher - ดึงแท่งเทียน M1 อย่างเดียวจาก yfinance (บอทนี้ดูแค่ timeframe เดียว)
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

MAX_RETRIES = 3
BASE_DELAY = 1.0

# ต้องมีแท่งพอสำหรับ EMA100 + lookback ต่าง ๆ (M1_EMA_SLOW=100 คือค่าที่มากสุด)
MIN_CANDLES_REQUIRED = 130


def fetch_m1(symbol: str) -> pd.DataFrame | None:
    """คืน DataFrame M1 (Open/High/Low/Close/Volume, index เป็นเวลา) หรือ None ถ้าดึงไม่สำเร็จ"""
    last_err = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ticker = yf.Ticker(symbol, session=_SESSION) if _SESSION else yf.Ticker(symbol)
            # yfinance จำกัด interval="1m" ย้อนหลังได้สูงสุด ~7 วัน - ขอ 5d ให้ปลอดภัย
            df = ticker.history(period="5d", interval="1m")
            if df is None or df.empty:
                raise RuntimeError("empty dataframe")
            df = df.dropna(subset=["Close"])
            if len(df) < MIN_CANDLES_REQUIRED:
                raise RuntimeError(f"too few candles ({len(df)})")
            return df
        except Exception as e:
            last_err = e
            # jitter delay กันโดน rate-limit ซ้ำ
            time.sleep(BASE_DELAY * attempt + random.uniform(0, 0.5))

    print(f"[data_fetcher] FAILED {symbol} M1: {last_err}")
    return None
