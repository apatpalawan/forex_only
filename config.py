"""
Config - Pure M1 Bot
ดูแค่ timeframe M1 อย่างเดียว ไม่สนใจ D1/H1/M15 อีกต่อไป

สัญญาณเดียว ต้องผ่านทุกเงื่อนไขพร้อมกันหมด (AND เข้มสุด สัญญาณน้อยมาก
แต่คุณภาพสูง) ไปทิศทางเดียวกันทั้งหมด - ทำทั้งขาขึ้น (BUY) และขาลง (SELL):

1. Sideway breakout (เกิดขึ้นล่าสุดภายใน N แท่ง)
2. EMA50 ตัด EMA100 (ยืนยัน trend ใหญ่ เกิดขึ้นล่าสุดภายใน N แท่ง เช่นกัน)
3. EMA9 ตัด EMA20 บนแท่งล่าสุด "หลัง" จุดตัด EMA50x100 ไปทิศทางเดียวกัน
   (pullback confirmation = จุดเข้าไม้จริง)
4. MACD ยืนยันทิศทาง (เส้น MACD อยู่เหนือ/ใต้ Signal)
5. RSI ยืนยันทิศทาง (RSI > 50 = ขึ้น, RSI < 50 = ลง)
6. ADX ยืนยันว่ากำลัง trend แรงพอ (ADX >= เกณฑ์) + DI+/DI- ยืนยันทิศทาง

หมายเหตุ: ไม่ใช้ Volume เป็นเงื่อนไขแล้ว (คู่เงิน Forex ส่วนใหญ่บน Yahoo
Finance ไม่มีข้อมูล Volume จริง - ตรวจสอบจริงแล้วด้วย check_symbol_volume.py
พบว่าคู่เงินทั้ง 28 คู่ที่เพิ่มเข้ามา Volume=0 หมด) ใช้ MACD/RSI/ADX
ยืนยันโมเมนตัมแทน ทำให้ทุกคู่เงินกลับมาใช้งานได้ตามปกติ

แก้ตัวเลขในไฟล์นี้ไฟล์เดียวเพื่อปรับพฤติกรรมบอท
"""

import os

# ── สัญลักษณ์ที่สแกน ────────────────────────────────────────────────
# ทองคำ (GC=F) + คู่เงินหลัก 28 คู่ (จาก 8 สกุลหลัก: EUR/GBP/AUD/NZD/
# USD/CAD/CHF/JPY) - กลับมาใช้ได้ทุกคู่แล้ว เพราะไม่ต้องพึ่ง Volume อีกต่อไป
SYMBOLS = [
    "GC=F",
    # --- EUR ---
    "EURGBP=X", "EURAUD=X", "EURNZD=X", "EURUSD=X",
    "EURCAD=X", "EURCHF=X", "EURJPY=X",
    # --- GBP ---
    "GBPAUD=X", "GBPNZD=X", "GBPUSD=X", "GBPCAD=X",
    "GBPCHF=X", "GBPJPY=X",
    # --- AUD ---
    "AUDNZD=X", "AUDUSD=X", "AUDCAD=X", "AUDCHF=X", "AUDJPY=X",
    # --- NZD ---
    "NZDUSD=X", "NZDCAD=X", "NZDCHF=X", "NZDJPY=X",
    # --- USD ---
    "USDCAD=X", "USDCHF=X", "USDJPY=X",
    # --- CAD / CHF ---
    "CADCHF=X", "CADJPY=X", "CHFJPY=X",
]

# ── M1: กรอบ sideway (ก่อนเกิด breakout) ─────────────────────────────
M1_SIDEWAY_LOOKBACK = 20              # จำนวนแท่ง M1 ที่ใช้หากรอบ sideway (ไม่รวมแท่งล่าสุดที่กำลังเช็ค breakout)
M1_SIDEWAY_MAX_RANGE_ATR_RATIO = 1.5  # (high-low ของกรอบ) / ATR(M1) ต้อง <= ค่านี้ ถึงจะถือว่าเป็น sideway จริง
M1_ATR_PERIOD = 14

# ── M1: breakout ──────────────────────────────────────────────────────
M1_BREAKOUT_BUFFER_PCT = 0.05         # ต้องทะลุกรอบเกินกี่% ถึงจะนับ (กัน false breakout จาก noise)

# ── M1: EMA cross (trend หลัก) ──────────────────────────────────────────
M1_EMA_FAST = 50
M1_EMA_SLOW = 100

# ── M1: EMA cross (pullback confirmation - จุดเข้าไม้จริง) ───────────────
M1_EMA_PULLBACK_FAST = 9
M1_EMA_PULLBACK_SLOW = 20

# แท่งตัด EMA50x100 (trend หลัก) และแท่ง breakout+volume ต้องเกิดขึ้น
# "ไม่เกินกี่แท่งก่อนหน้า" จุดตัด EMA9x20 (แท่งที่ยิงสัญญาณจริง) ถึงจะนับ
# ว่ายังเป็นเหตุการณ์เดียวกัน (ไม่ใช่เรื่องเก่าเกินไปที่ไม่เกี่ยวข้องกันแล้ว)
M1_PULLBACK_LOOKBACK_BARS = 30

# ── M1: MACD ─────────────────────────────────────────────────────────────
M1_MACD_FAST = 12
M1_MACD_SLOW = 26
M1_MACD_SIGNAL = 9

# ── M1: RSI ──────────────────────────────────────────────────────────────
M1_RSI_PERIOD = 14
M1_RSI_BULL_THRESHOLD = 50   # RSI > ค่านี้ ถึงจะยืนยันขาขึ้น
M1_RSI_BEAR_THRESHOLD = 50   # RSI < ค่านี้ ถึงจะยืนยันขาลง

# ── M1: ADX + DI ─────────────────────────────────────────────────────────
M1_ADX_PERIOD = 14
M1_ADX_MIN = 20               # ADX ต้อง >= ค่านี้ ถึงจะถือว่า trend แรงพอ (ไม่ใช่ตลาดไม่มีทิศทาง)

# ── ตัวกรอง Session (เทรดเฉพาะช่วงสภาพคล่องสูง) ───────────────────────
# เวลาเป็น UTC, ค่า default ครอบคลุม London + London/NY overlap
SESSION_FILTER_ENABLED = True
SESSION_START_UTC = 7     # London open ~07:00 UTC
SESSION_END_UTC = 16      # หลัง NY overlap เริ่มเบาลง ~16:00 UTC
# ปรับเป็นเวลาไทย (UTC+7) เอง: 07-16 UTC = 14:00-23:00 ไทย

# ── ตัวกรองข่าว (ปิดไว้ก่อนโดย default) ────────────────────────────────
NEWS_FILTER_ENABLED = False
NEWS_BLOCK_MINUTES_BEFORE = 30
NEWS_BLOCK_MINUTES_AFTER = 15
FOREX_FACTORY_JSON_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# ── Money management guardrails (แจ้งเตือนอย่างเดียว ไม่ auto trade) ───────
# M1 เกิดสัญญาณได้บ่อยกว่า D1/H1/M15 เดิมมาก จึงตั้งเพดานสูงกว่าเดิม (เดิม 3)
MAX_ALERTS_PER_SYMBOL_PER_DAY = 10

# ── LINE ─────────────────────────────────────────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_TARGET_IDS = [
    t.strip() for t in os.environ.get("LINE_TARGET_IDS", "").split(",") if t.strip()
]

# ── State file (dedupe กันแจ้งเตือนซ้ำแท่งเดิม) ───────────────────────
STATE_FILE = "state.json"
