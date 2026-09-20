import os

# ===== คู่เงินยอดนิยม + ทองคำ =====
# key = ชื่อที่ใช้แสดงผล (และใช้ในข้อความ LINE), value = ticker บน Yahoo Finance (yfinance)
# หมายเหตุ: XAUUSD=X ไม่มีข้อมูล M1 บน Yahoo (คืน HTTP 404) จึงใช้ GC=F (COMEX gold futures)
# แทนในการดึงข้อมูล แต่ยังแสดงผลเป็น "XAUUSD" ในข้อความแจ้งเตือน
SYMBOLS = {
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
    "XAUUSD": "GC=F",  # gold, ใช้ futures ticker เพราะ XAUUSD=X ไม่มีข้อมูล M1
}

# ===== Timeframe =====
INTERVAL = "1m"
RANGE = "5d"  # yfinance จำกัด M1 ย้อนหลังได้ไม่เกิน ~7 วัน

# ===== เงื่อนไขเทรนด์หลัก: EMA100 ตัด EMA300 =====
EMA_TREND_FAST = 100
EMA_TREND_SLOW = 300
# ระยะย้อนหลังสูงสุดที่จะมองหาจุดตัด EMA100/300 ล่าสุด เพื่อยืนยันว่าเพิ่งเกิดเทรนด์นี้จริง
# (ถ้าหาจุดตัดไม่เจอในช่วงนี้ จะ fallback ไปใช้ทิศทางปัจจุบันของ EMA100 vs EMA300 แทน)
TREND_CROSS_LOOKBACK_BARS = 300

# ===== เงื่อนไขสัญญาณ: EMA9 เรียงตัวกับ EMA25 (เช็คสถานะปัจจุบัน ไม่ต้องตัดกันใหม่) =====
EMA_SIGNAL_FAST = 9
EMA_SIGNAL_SLOW = 25

# ===== เงื่อนไขยืนยัน: MACD =====
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ===== เงื่อนไขยืนยัน: RSI =====
RSI_PERIOD = 14
RSI_MID = 50  # RSI > 50 = ฝั่งขึ้น, RSI < 50 = ฝั่งลง

# ===== เงื่อนไขยืนยัน: ADX/DI =====
ADX_PERIOD = 14
ADX_MIN = 20  # ADX ต้อง >= ค่านี้ถึงจะถือว่าเทรนด์มีแรงพอ (กันสัญญาณช่วงตลาดนิ่ง)

# ===== LINE Messaging API =====
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
# ถ้าต้องการส่งแบบ push ไปหา user/group เฉพาะ (แทนการ broadcast ไปทุกคนที่แอด OA)
# ตั้ง secret ชื่อ LINE_TARGET_IDS เป็น user id คั่นด้วย comma เช่น "Uxxxx,Uyyyy"
LINE_TARGET_IDS = os.environ.get("LINE_TARGET_IDS", "")

STATE_FILE = "state.json"

# หน่วงเวลาระหว่างสัญลักษณ์ (วินาที) กัน rate-limit ตอนดึงข้อมูลหลายตัวติดกัน
SYMBOL_FETCH_DELAY_SEC = 1.5
