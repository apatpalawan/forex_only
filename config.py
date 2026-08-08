import os

# ===== คู่เงินยอดนิยม + ทองคำ =====
# key = ชื่อที่ใช้แสดงผล, value = ticker บน Yahoo Finance (yfinance)
FOREX_SYMBOLS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "NZDUSD": "NZDUSD=X",
    "USDCHF": "USDCHF=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
    "EURGBP": "EURGBP=X",
    "XAUUSD": "XAUUSD=X",  # ทองคำ (spot gold)
}

# ===== พารามิเตอร์ D1: เช็คว่ามี price action ทั้งขาขึ้นและขาลง =====
D1_LOOKBACK = 20  # ดูย้อนหลังกี่แท่ง D1
D1_MIN_ATR_PCT = 0.003  # ATR(D1) ต้อง >= 0.3% ของราคา ไม่งั้นถือว่าตลาดนิ่งเกินไป ไม่น่าสนใจ
D1_SWING_MIN_RATIO = 1.5  # ขาขึ้น/ขาลงแต่ละขา ต้องมีขนาด >= 1.5 เท่าของ ATR(D1) ถึงจะนับว่าเป็น "price action ชัดเจน"

# ===== พารามิเตอร์ H1: เช็คว่าอยู่ในช่วง sideway =====
H1_LOOKBACK = 20  # ดูย้อนหลังกี่แท่ง H1 เพื่อหากรอบ sideway
H1_MAX_RANGE_ATR_RATIO = 2.5  # ความกว้างกรอบ (High สูงสุด - Low ต่ำสุด) ต้อง <= 2.5 เท่าของ ATR(H1)
BREAKOUT_BUFFER_ATR = 0.15  # ราคาต้องหลุดกรอบเกิน buffer นี้ (กัน false breakout / noise)

# ===== พารามิเตอร์แจ้งเตือนทันทีเมื่อ D1 เคลื่อนไหวรุนแรงกระทันหัน =====
SUDDEN_MOVE_ATR_RATIO = 2.0  # ถ้า range ของแท่ง D1 วันนี้ >= 2 เท่าของ ATR(D1) ถือว่า "แรงกระทันหัน"

# ===== LINE Messaging API =====
# ใส่เป็น GitHub Secret ชื่อ LINE_CHANNEL_ACCESS_TOKEN แล้ว workflow จะ inject เป็น env var ให้เอง
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

# ถ้าต้องการส่งแบบ push ไปหา user/group เฉพาะ (แทนการ broadcast ไปทุกคนที่แอด OA)
# ให้ตั้ง secret ชื่อ LINE_TARGET_IDS เป็น user id คั่นด้วย comma เช่น "Uxxxx,Uyyyy"
LINE_TARGET_IDS = os.environ.get("LINE_TARGET_IDS", "")

STATE_FILE = "state.json"

# ===== เวลาที่จะ "ส่ง" สรุปคู่เงินที่เก็บสะสมไว้ (เวลาไทย, 24 ชม. รูปแบบ "HH:MM") =====
SEND_TIMES = ["08:00", "10:00", "13:00", "15:00", "19:00"]

# ยอมรับความคลาดเคลื่อนของเวลาได้กี่นาที (กัน cron ของ GitHub Actions รันไม่ตรงเป๊ะ)
SEND_TIME_TOLERANCE_MIN = 10

# key ใน state.json ที่ใช้เก็บคู่เงินที่เจอแล้วรอส่ง
PENDING_KEY = "_pending"
LAST_SENT_SLOT_KEY = "_last_sent_slot"
