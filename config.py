"""
Config - M1 Trigger Bot (D1 -> H1 -> M15 -> M1)
แก้ตัวเลขในไฟล์นี้ไฟล์เดียวเพื่อปรับพฤติกรรมบอท
"""

import os

# ── สัญลักษณ์ที่สแกน ────────────────────────────────────────────────
# เฉพาะทองคำเท่านั้น
SYMBOLS = [
    "XAUUSD=X",
]

# ── D1: หาทิศทางหลัก ────────────────────────────────────────────────
EMA_FAST = 20
EMA_SLOW = 50
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ── H1: ยืนยันความแข็งแรงของเทรนด์ ──────────────────────────────────
ADX_PERIOD = 14
ADX_MIN = 25.0          # ADX ต้อง > ค่านี้
ADX_MUST_RISE = True    # ADX ต้องเพิ่มขึ้นจากแท่งก่อนหน้า
ATR_PERIOD = 14
ATR_LOOKBACK_AVG = 50   # ใช้หาค่าเฉลี่ย ATR ย้อนหลังกี่แท่ง
ATR_RATIO_MIN = 1.0     # ATR ปัจจุบัน / ATR เฉลี่ย ต้อง >= ค่านี้
DI_GAP_MIN = 5.0        # |DI+ - DI-| ต้อง >= ค่านี้ (ความชัดของทิศทาง)

# ── M15: หาโซน pullback + price action reversal ─────────────────────
PULLBACK_EMA_TOLERANCE_PCT = 0.15   # ราคาต้องห่างจาก EMA20(M15) ไม่เกินกี่% ถึงจะนับว่า "ย่อเข้าใกล้"
M15_LOOKBACK_BARS = 30              # ดูย้อนหลังกี่แท่ง M15 เพื่อหาแท่งกลับตัวล่าสุด

# ── M1: จุด trigger เข้าไม้ ──────────────────────────────────────────
# M1 ใช้แค่ "ยืนยันแท่งปิด" ว่าราคาทะลุ high/low ของโซน M15 reversal จริง
# ไม่ใช้ indicator ใด ๆ เพิ่มบน M1 ตามหลักการที่คุยกันไว้
M1_CONFIRM_WINDOW_BARS = 15         # ต้องเกิด breakout ภายในกี่แท่ง M1 หลังโซน M15 พร้อม ไม่งั้นถือว่าโซนหมดอายุ

# ── ตัวกรอง Session (เทรดเฉพาะช่วงสภาพคล่องสูง) ───────────────────────
# เวลาเป็น UTC, ค่า default ครอบคลุม London + London/NY overlap
SESSION_FILTER_ENABLED = True
SESSION_START_UTC = 7     # London open ~07:00 UTC
SESSION_END_UTC = 16      # หลัง NY overlap เริ่มเบาลง ~16:00 UTC
# ปรับเป็นเวลาไทย (UTC+7) เอง: 07-16 UTC = 14:00-23:00 ไทย

# ── ตัวกรองความผันผวนผิดปกติ (proxy แทน spread จริงที่ยังไม่มี broker API) ─
SKIP_IF_M1_RANGE_RATIO_ABOVE = 3.0  # ถ้าแท่ง M1 ล่าสุดกว้างผิดปกติ (เทียบ ATR M1 เฉลี่ย) ให้ข้าม กันช่วง spike ข่าว

# ── ตัวกรองข่าว (ปิดไว้ก่อนโดย default, เปิดถ้าต้องการเชื่อม calendar) ─────
NEWS_FILTER_ENABLED = False
NEWS_BLOCK_MINUTES_BEFORE = 30
NEWS_BLOCK_MINUTES_AFTER = 15
FOREX_FACTORY_JSON_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# ── Money management guardrails (แจ้งเตือนอย่างเดียว ไม่ auto trade) ───────
MAX_ALERTS_PER_SYMBOL_PER_DAY = 3   # กัน over-alert จากบอทตัวเดียวกันซ้ำ ๆ ในคู่เดิม

# ── LINE ─────────────────────────────────────────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_TARGET_IDS = [
    t.strip() for t in os.environ.get("LINE_TARGET_IDS", "").split(",") if t.strip()
]

# ── State file (dedupe กันแจ้งเตือนซ้ำแท่งเดิม) ───────────────────────
STATE_FILE = "state.json"
