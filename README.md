# Pure M1 Bot → แจ้งเตือนเข้า LINE OA

บอทดู **timeframe M1 อย่างเดียว** ไม่สนใจ D1/H1/M15

สัญญาณเดียว ต้องผ่าน **ทุกเงื่อนไขพร้อมกันหมด** (AND เข้มสุด → สัญญาณน้อยมาก แต่คุณภาพสูง) ไปทิศทางเดียวกันทั้งหมด (BUY/SELL):

1. **Sideway breakout + Volume momentum** — ราคาสร้างกรอบแคบแล้วทะลุออก พร้อม Volume พุ่ง
2. **EMA50 ตัด EMA100** — ยืนยัน trend หลัก
3. **EMA9 ตัด EMA20** (pullback confirmation) — ต้องเกิด **"หลัง"** จุดตัด EMA50×100 (ข้อ 2) ไปทิศทางเดียวกัน แท่งนี้คือจุดยิงสัญญาณจริง
4. **MACD** — เส้น MACD อยู่เหนือ/ใต้ Signal ตรงทิศทาง
5. **RSI** — RSI > 50 (ขึ้น) หรือ RSI < 50 (ลง)
6. **ADX + DI** — ADX ≥ เกณฑ์ (trend แรงพอ) และ DI+/DI- ยืนยันทิศทาง

ข้อ 1-3 ต้องเกิดขึ้นภายในกรอบเวลาเดียวกัน (`M1_PULLBACK_LOOKBACK_BARS`) ข้อ 4-6 เช็คที่แท่งยิงสัญญาณ (ข้อ 3) เท่านั้น

## โครงสร้างไฟล์

```
config.py               พารามิเตอร์ทั้งหมด — ปรับได้ตรงนี้
lib/data_fetcher.py     ดึงราคา M1 จาก Yahoo Finance (yfinance)
lib/indicators.py       EMA / MACD / RSI / ADX+DI / ATR (pandas ล้วน)
lib/strategy.py         logic รวมเงื่อนไข AND ทั้ง 6 ข้อ
lib/session_filter.py   จำกัดช่วงเวลาเทรด (London/NY overlap)
lib/news_filter.py      (ปิดไว้โดย default) ระงับแจ้งเตือนช่วงข่าวแรงถ้าเปิดใช้
lib/state_manager.py    อ่าน/บันทึก state.json กันแจ้งเตือนซ้ำแท่งเดิม
lib/line_notify.py      ส่งข้อความเข้า LINE (รูปแบบสั้น)
main.py                 สแกนหลัก รันตาม cron ใน .github/workflows/m1_trigger.yml (ทุก 5 นาที)
state.json              เก็บสถานะแจ้งเตือน (bot commit กลับ repo เองอัตโนมัติ)
test_local.py           ทดสอบ logic แบบ offline (ไม่ต้องต่อ internet)
check_symbol_volume.py  เช็คว่า symbol ไหนมี Volume จริงใช้งานได้ (ต้องต่อ internet)
```

## ⚠️ ข้อควรระวังสำคัญเรื่อง Volume

บอทนี้ **ต้องมี Volume จริง** ถึงจะทำงานได้ เพราะเงื่อนไข "volume momentum" เป็นส่วนหนึ่งของ AND ที่บังคับ
คู่เงิน Forex ส่วนใหญ่บน Yahoo Finance (ticker ลงท้าย `=X`) เป็น **synthetic FX cross** ที่ไม่มีข้อมูล
Volume จริง (มักเป็น 0 ตลอด) เพราะตลาด Forex เป็น OTC ไม่มีการรายงาน volume รวมศูนย์

`config.SYMBOLS` ตอนนี้มี **ทองคำ (`GC=F`)** + **คู่เงินหลัก 28 คู่** (จาก 8 สกุล: EUR/GBP/AUD/NZD/USD/CAD/CHF/JPY)
**ก่อนใช้จริง แนะนำให้รัน `python check_symbol_volume.py` บนเครื่องที่ต่อ internet ได้ก่อนเสมอ** เพื่อดูว่าคู่เงินไหน
มี volume ใช้งานได้จริงบ้าง แล้วตัดคู่ที่ไม่มี volume ออกจาก `config.SYMBOLS` (จะได้ไม่เปลืองรอบสแกนกับ symbol
ที่ไม่มีทางส่งสัญญาณอยู่แล้ว)

## ทำไมต้องผ่านทุกเงื่อนไข (AND เข้มสุด)

ตามที่ตกลงกันไว้ — เพื่อกรองสัญญาณหลอกให้เหลือน้อยที่สุด บอทจะรอให้ทั้ง 3 โครงสร้างราคา (breakout, trend
EMA ใหญ่, pullback EMA เล็ก) และโมเมนตัม/ความแรงเทรนด์ (MACD, RSI, ADX) เห็นตรงกันหมดก่อนถึงจะแจ้งเตือน
แลกกับความถี่สัญญาณที่น้อยลงมาก แต่คุณภาพสูงขึ้น

## ขั้นตอนติดตั้ง / ทดสอบ

```
pip install -r requirements.txt
export LINE_CHANNEL_ACCESS_TOKEN="your-token"
export LINE_TARGET_IDS="your-user-id"
python test_local.py            # ทดสอบ logic แบบ offline ก่อนเสมอ
python check_symbol_volume.py   # เช็ค volume จริงของแต่ละ symbol ก่อนใช้จริง (ต้องต่อ internet)
python main.py                  # รันจริง 1 รอบ (ต้องต่อ internet)
```

ถ้าไม่ตั้ง `LINE_CHANNEL_ACCESS_TOKEN`/`LINE_TARGET_IDS` บอทจะข้ามการส่งจริงและ print แจ้งเหตุผลออกทาง console แทน

## ปรับพารามิเตอร์

เปิด `config.py`:
- `SYMBOLS` — รายชื่อ symbol ที่สแกน (ต้องมี Volume จริงตามที่อธิบายด้านบน)
- `M1_SIDEWAY_LOOKBACK`, `M1_SIDEWAY_MAX_RANGE_ATR_RATIO` — ความ "แคบ" ของกรอบ sideway
- `M1_BREAKOUT_BUFFER_PCT` — กัน false breakout
- `M1_VOLUME_LOOKBACK`, `M1_VOLUME_RATIO_MIN` — เกณฑ์ volume momentum
- `M1_EMA_FAST` / `M1_EMA_SLOW` — EMA trend หลัก (default 50/100)
- `M1_EMA_PULLBACK_FAST` / `M1_EMA_PULLBACK_SLOW` — EMA pullback confirmation (default 9/20)
- `M1_PULLBACK_LOOKBACK_BARS` — กรอบเวลาที่ยอมให้ breakout/EMA50x100 "เก่า" ได้ก่อนแท่งยิงสัญญาณ
- `M1_MACD_FAST/SLOW/SIGNAL`, `M1_RSI_PERIOD`, `M1_RSI_BULL/BEAR_THRESHOLD`, `M1_ADX_PERIOD`, `M1_ADX_MIN`
- `MAX_ALERTS_PER_SYMBOL_PER_DAY` — เพดานแจ้งเตือนต่อ symbol ต่อวัน

## ข้อจำกัดที่ควรรู้

1. **GitHub Actions cron ต่ำสุดจริงคือ ~5 นาที** (และอาจดีเลย์เพิ่มอีก 2-10 นาที) ไม่ใช่ 1 นาทีเป๊ะ
2. **ข้อมูลจาก yfinance ไม่ใช่ real-time tick data จริง** อาจมี delay หรือช่วงข้อมูลขาดหาย
3. **สแกน 29 symbols ต่อรอบ** — เพิ่ม `time.sleep()` สั้น ๆ ระหว่าง symbol ใน `main.py` กัน rate-limit แล้ว
   แต่ถ้าเจอปัญหาโดนบล็อกให้เพิ่มค่า `INTER_SYMBOL_DELAY_SEC` ใน `main.py`
4. **นี่คือเครื่องมือช่วยหาโอกาส ไม่ใช่คำแนะนำการลงทุน** สัญญาณหลอกเกิดขึ้นได้เสมอแม้เงื่อนไขจะเข้มมากแล้ว
ควรใช้ร่วมกับการบริหารความเสี่ยงของคุณเอง (stop loss, money management)
