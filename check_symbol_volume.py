"""
check_symbol_volume.py - เครื่องมือตรวจสอบว่า symbol ไหนใน config.SYMBOLS
มีข้อมูล Volume จริงบน Yahoo Finance ใช้งานได้ (ไม่ใช่ 0 ตลอด)

ต้องต่อ internet จริงถึงจะรันได้ (สคริปต์ในนี้ทดสอบแบบ offline ไม่ได้
เพราะต้องดึงข้อมูลจริงจาก Yahoo Finance) - รันบนเครื่องคุณเองก่อนใช้จริง
เพื่อดูว่าคู่เงินไหน "มีสิทธิ์" ส่งสัญญาณได้บ้าง (เงื่อนไข volume
momentum เป็นส่วนหนึ่งของ AND ที่บอทบังคับผ่านทุกตัว)

วิธีรัน:
    python check_symbol_volume.py
"""

import time
import config
from lib.data_fetcher import fetch_m1

USABLE = []
UNUSABLE = []
FAILED = []

print(f"กำลังตรวจสอบ {len(config.SYMBOLS)} symbols ... (อาจใช้เวลาสักครู่)\n")

for symbol in config.SYMBOLS:
    df = fetch_m1(symbol)
    if df is None or df.empty:
        FAILED.append(symbol)
        print(f"[ดึงข้อมูลไม่สำเร็จ] {symbol}")
        time.sleep(0.5)
        continue

    recent_volume = df["Volume"].tail(50)
    nonzero_ratio = (recent_volume > 0).mean()
    avg_volume = recent_volume.mean()

    if nonzero_ratio >= 0.5 and avg_volume > 0:
        USABLE.append(symbol)
        print(f"[ใช้ได้]     {symbol:12} avg_volume={avg_volume:.1f}  nonzero={nonzero_ratio*100:.0f}%")
    else:
        UNUSABLE.append(symbol)
        print(f"[ไม่มี volume จริง] {symbol:12} avg_volume={avg_volume:.1f}  nonzero={nonzero_ratio*100:.0f}%")

    time.sleep(0.5)

print()
print("=" * 60)
print(f"สรุป: ใช้ได้ {len(USABLE)} / ไม่มี volume จริง {len(UNUSABLE)} / ดึงไม่สำเร็จ {len(FAILED)}")
print("=" * 60)
print()
print("Symbol ที่มี volume ใช้งานได้จริง (แนะนำให้เก็บไว้ใน config.SYMBOLS):")
print(USABLE)
print()
print("Symbol ที่ไม่มี volume จริง (บอทจะไม่มีวันส่งสัญญาณให้ symbol พวกนี้ -")
print("แนะนำให้ตัดออกจาก config.SYMBOLS เพื่อไม่เปลืองรอบสแกนเปล่า ๆ):")
print(UNUSABLE)

if FAILED:
    print()
    print("Symbol ที่ดึงข้อมูลไม่สำเร็จเลย (เช็ค ticker name หรือลองรันใหม่):")
    print(FAILED)
