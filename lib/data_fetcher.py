"""
ดึงข้อมูลราคา M1 จาก Yahoo Finance (yfinance)
ใช้ curl_cffi session แบบ impersonate browser กัน rate-limit/block บน shared IP ของ GitHub Actions
ตัดแท่งสุดท้ายที่ยังไม่ปิด (unclosed candle) ออกเสมอ เพื่อไม่ให้อินดิเคเตอร์คำนวณจากแท่งที่ยังไม่จบ
"""
import time
import random

import pandas as pd
import yfinance as yf

try:
    from curl_cffi import requests as curl_requests
    _HAS_CURL_CFFI = True
except ImportError:
    _HAS_CURL_CFFI = False


def _make_session():
    if not _HAS_CURL_CFFI:
        return None
    return curl_requests.Session(impersonate="chrome")


def fetch_m1(ticker: str, interval: str, period: str, max_retries: int = 3) -> pd.DataFrame:
    """
    คืน DataFrame คอลัมน์ Open/High/Low/Close/Volume, index เป็นเวลา (ตัดแท่งสุดท้ายที่ยังไม่ปิดออกแล้ว)
    คืน DataFrame ว่างถ้าดึงไม่สำเร็จหลัง retry ครบ
    """
    last_err = None
    for attempt in range(max_retries):
        try:
            session = _make_session()
            tk = yf.Ticker(ticker, session=session) if session else yf.Ticker(ticker)
            df = tk.history(interval=interval, period=period, auto_adjust=False)

            if df is None or df.empty:
                raise ValueError("empty dataframe")

            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(
                subset=["Open", "High", "Low", "Close"]
            )

            # ตัดแท่งสุดท้ายทิ้งเสมอ เพราะแท่ง M1 ล่าสุดที่ yfinance คืนมามักยังไม่ปิดจริง
            if len(df) > 1:
                df = df.iloc[:-1]

            if df.empty:
                raise ValueError("dataframe empty after dropping unclosed candle")

            return df

        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(1.0 + random.random() * 1.5)

    print(f"[data_fetcher] fetch failed for {ticker}: {last_err}")
    return pd.DataFrame()
