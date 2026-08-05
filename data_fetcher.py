"""
ดึงข้อมูลราคา OHLC จาก Yahoo Finance ผ่าน yfinance
หมายเหตุ: yfinance เป็นข้อมูลไม่เป็นทางการจาก Yahoo Finance ไม่ใช่ real-time tick data แท้ๆ
อาจมี delay เล็กน้อยหรือข้อมูลขาดหายบางช่วง โดยเฉพาะคู่เงิน/ทองที่เทรดนอกตลาดหลัก (OTC)
ถ้าต้องการความแม่นยำสูงขึ้นสำหรับใช้เทรดจริง ควรพิจารณาเปลี่ยนไปใช้ API ที่มี key เช่น Twelve Data / OANDA

ใช้ curl_cffi impersonate browser + jitter delay + retry เพื่อกัน Yahoo rate-limit/block
บน shared IP ของ GitHub Actions (เจอปัญหานี้มาแล้วกับบอทหลัก forex-radar-v8)
"""
import random
import time

import pandas as pd
import yfinance as yf
from curl_cffi import requests as cffi_requests

_session = cffi_requests.Session(impersonate="chrome")

MAX_RETRIES = 3
BASE_DELAY = 1.5  # วินาที, คูณเพิ่มตามจำนวนครั้งที่ retry (backoff)


def fetch_ohlc(symbol_yf, interval, period):
    """
    ดึงข้อมูลแท่งเทียน
    interval: '1d' สำหรับ D1, '60m' สำหรับ H1
    period: ช่วงเวลาย้อนหลัง เช่น '6mo', '60d'
    """
    for attempt in range(1, MAX_RETRIES + 1):
        # jitter เล็กน้อยก่อนยิงทุกครั้ง กันหลายสัญลักษณ์ยิงถี่ติดกันเกินไป
        time.sleep(random.uniform(0.3, 0.9))

        try:
            df = yf.download(
                symbol_yf,
                interval=interval,
                period=period,
                progress=False,
                auto_adjust=False,
                session=_session,
            )
        except Exception as e:
            print(f"[ERROR] fetch_ohlc {symbol_yf} {interval} (ครั้งที่ {attempt}): {e}")
            df = None

        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]
            return df.dropna()

        if attempt < MAX_RETRIES:
            time.sleep(BASE_DELAY * attempt + random.uniform(0, 1.0))

    print(f"[WARN] fetch_ohlc {symbol_yf} {interval}: ไม่ได้ข้อมูลหลังลอง {MAX_RETRIES} ครั้ง")
    return None
