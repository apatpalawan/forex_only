"""
Config - Pure M1 Bot
ดูแค่ timeframe M1 อย่างเดียว ไม่สนใจ D1/H1/M15 อีกต่อไป

สัญญาณเดียว: "sideway breakout + volume momentum" ต้องเกิดพร้อมกันกับ
"EMA50 ตัด EMA100" บนแท่ง M1 เดียวกัน และไปทิศทางเดียวกัน (AND ไม่ใช่ OR)
ทำทั้งขาขึ้น (BUY) และขาลง (SELL)

แก้ตัวเลขในไฟล์นี้ไฟล์เดียวเพื่อปรับพฤติกรรมบอท
"""

import os

# ── สัญลักษณ์ที่สแกน ────────────────────────────────────────────────
# หมายเหตุสำคัญ: เปลี่ยนจาก "XAUUSD=X" (FX cross สังเคราะห์ของ Yahoo)
# เป็น "GC=F" (สัญญาซื้อขายล่วงหน้าทองคำ) เพราะ Volume ของ "XAUUSD=X"
# บนเว็บ Yahoo Finance มักเป็น 0 เกือบตลอด (Forex OTC ไม่มี volume จริง
# ตามมาตรฐานสากล) ซึ่งจะทำให้เงื่อนไข "volume momentum" ไม่มีทางผ่านได้
# เลย และบอทนี้ต้องการทั้ง breakout+volume "และ" EMA cross พร้อมกันถึง
# จะแจ้งเตือน (AND ไม่ใช่ OR) - ถ้าไม่มี volume ที่ใช้งานได้ บอทจะไม่มี
# ทางส่งสัญญาณเลย ถ้าจะกลับไปใช้ "XAUUSD=X" หรือเพิ่มคู่เงิน Forex อื่น
# ให้รู้ไว้ว่า Volume ของคู่เงิน Forex ส่วนใหญ่บน Yahoo ก็ไม่น่าเชื่อถือ
# เช่นกัน (ทดสอบ/สังเกตค่าจริงก่อนใช้เทรดจริงเสมอ)
SYMBOLS = [
    "GC=F",
]

# ── M1: กรอบ sideway (ก่อนเกิด breakout) ─────────────────────────────
M1_SIDEWAY_LOOKBACK = 20              # จำนวนแท่ง M1 ที่ใช้หากรอบ sideway (ไม่รวมแท่งล่าสุดที่กำลังเช็ค breakout)
M1_SIDEWAY_MAX_RANGE_ATR_RATIO = 1.5  # (high-low ของกรอบ) / ATR(M1) ต้อง <= ค่านี้ ถึงจะถือว่าเป็น sideway จริง
M1_ATR_PERIOD = 14

# ── M1: breakout ──────────────────────────────────────────────────────
M1_BREAKOUT_BUFFER_PCT = 0.05         # ต้องทะลุกรอบเกินกี่% ถึงจะนับ (กัน false breakout จาก noise)

# ── M1: volume momentum ───────────────────────────────────────────────
M1_VOLUME_LOOKBACK = 20               # ค่าเฉลี่ย Volume ย้อนหลังกี่แท่ง (ไม่รวมแท่งล่าสุด)
M1_VOLUME_RATIO_MIN = 1.5             # Volume แท่งล่าสุด >= กี่เท่าของค่าเฉลี่ย ถึงจะนับว่า "momentum"

# ── M1: EMA cross ──────────────────────────────────────────────────────
M1_EMA_FAST = 50
M1_EMA_SLOW = 100

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
