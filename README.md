# Pure M1 Bot → แจ้งเตือนเข้า LINE OA

บอทดู **timeframe M1 อย่างเดียว** ไม่สนใจ D1/H1/M15 อีกต่อไป (เปลี่ยนจากเวอร์ชันก่อนหน้าที่ไล่ยืนยันหลาย timeframe)

ส่งสัญญาณ **1 แบบเท่านั้น** และต้องเกิด **ทั้ง 2 เงื่อนไขพร้อมกัน** บนแท่ง M1 ที่ปิดล่าสุดแท่งเดียวกัน (AND ไม่ใช่ OR):

1. **Sideway breakout + Volume momentum** — ราคาสร้างกรอบแคบ (sideway) มาสักพัก แล้วแท่งล่าสุดปิดทะลุกรอบ พร้อม Volume พุ่งขึ้นเทียบค่าเฉลี่ย
2. **EMA50 ตัด EMA100** — เส้น EMA50 ตัดขึ้น/ลงผ่านเส้น EMA100 บนแท่งเดียวกันนั้นพอดี

ทั้งสองเงื่อนไขต้องไปทิศทางเดียวกันด้วย (breakout ขึ้น + EMA ตัดขึ้น = BUY, breakout ลง + EMA ตัดลง = SELL) ทำทั้งขาขึ้นและขาลง ข้อความ LINE สั้น ประหยัดโควตา

## โครงสร้างไฟล์

```
config.py               พารามิเตอร์ทั้งหมด (symbol, threshold ต่างๆ) — ปรับได้ตรงนี้
lib/data_fetcher.py     ดึงราคา M1 จาก Yahoo Finance (yfinance)
lib/indicators.py       EMA / ATR (คำนวณด้วย pandas ล้วน)
lib/strategy.py         logic: หากรอบ sideway, เช็ค breakout, เช็ค volume momentum, เช็ค EMA cross, รวมเงื่อนไข AND
lib/session_filter.py   จำกัดช่วงเวลาเทรด (London/NY overlap)
lib/news_filter.py      (ปิดไว้โดย default) ระงับแจ้งเตือนช่วงข่าวแรงถ้าเปิดใช้
lib/state_manager.py    อ่าน/บันทึก state.json กันแจ้งเตือนซ้ำแท่งเดิม
lib/line_notify.py      ส่งข้อความเข้า LINE (รูปแบบสั้น)
main.py                 สแกนหลัก รันตาม cron ใน .github/workflows/m1_trigger.yml (ทุก 5 นาที)
state.json              เก็บสถานะแจ้งเตือน (bot commit กลับ repo เองอัตโนมัติ)
test_local.py           ทดสอบ logic แบบ offline (ไม่ต้องต่อ internet)
```

## ⚠️ ข้อควรระวังสำคัญเรื่อง Volume

บอทนี้ **ต้องมี Volume จริง** ถึงจะทำงานได้ เพราะเงื่อนไข "volume momentum" เป็นส่วนหนึ่งของ AND ที่บังคับ
คู่เงิน Forex ส่วนใหญ่บน Yahoo Finance (เช่น `EURUSD=X`, `XAUUSD=X`) เป็น **synthetic FX cross** ที่ไม่มีข้อมูล
Volume จริง (มักเป็น 0 ตลอด) เพราะตลาด Forex เป็น OTC ไม่มีการรายงาน volume รวมศูนย์

`config.py` จึงตั้ง default เป็น **`GC=F`** (สัญญาซื้อขายล่วงหน้าทองคำ) แทน `XAUUSD=X` เดิม เพราะมี Volume จริง
ถ้าจะเพิ่ม/เปลี่ยน symbol อื่น ให้ทดสอบก่อนว่า Volume ของ ticker นั้นบน yfinance ไม่ใช่ 0 ตลอด ไม่งั้นสัญญาณจะไม่มีวันเกิดขึ้นเลย

## ทำไม 2 เงื่อนไขต้องเกิดพร้อมกัน (AND)

ตามที่ตกลงกันไว้ — สัญญาณ breakout เดี่ยว ๆ หรือ EMA cross เดี่ยว ๆ อาจเป็น noise ได้ง่ายบน timeframe เล็กอย่าง M1
การบังคับให้ทั้งสองเงื่อนไข (โครงสร้างราคา + โมเมนตัม + trend confirmation จาก EMA) เกิดพร้อมกันบนแท่งเดียวกัน
ช่วยกรองสัญญาณหลอกได้มากกว่า แลกกับความถี่สัญญาณที่น้อยลง

## ขั้นตอนติดตั้ง / ทดสอบ

```
pip install -r requirements.txt
export LINE_CHANNEL_ACCESS_TOKEN="your-token"
export LINE_TARGET_IDS="your-user-id"
python test_local.py     # ทดสอบ logic แบบ offline ก่อนเสมอ
python main.py            # รันจริง 1 รอบ (ต้องต่อ internet)
```

ถ้าไม่ตั้ง `LINE_CHANNEL_ACCESS_TOKEN`/`LINE_TARGET_IDS` บอทจะข้ามการส่งจริงและ print แจ้งเหตุผลออกทาง console แทน

## ปรับพารามิเตอร์

เปิด `config.py`:
- `SYMBOLS` — รายชื่อ symbol ที่สแกน (ต้องมี Volume จริงตามที่อธิบายด้านบน)
- `M1_SIDEWAY_LOOKBACK`, `M1_SIDEWAY_MAX_RANGE_ATR_RATIO` — ความ "แคบ" ของกรอบ sideway ที่ต้องการ
- `M1_BREAKOUT_BUFFER_PCT` — กัน false breakout (ยิ่งสูงยิ่งรอ confirm มากขึ้น แต่เข้าช้าลง)
- `M1_VOLUME_LOOKBACK`, `M1_VOLUME_RATIO_MIN` — เกณฑ์ volume momentum
- `M1_EMA_FAST` / `M1_EMA_SLOW` — ค่าเริ่มต้น 50/100 ตามที่ตกลงกันไว้
- `MAX_ALERTS_PER_SYMBOL_PER_DAY` — เพดานแจ้งเตือนต่อ symbol ต่อวัน

## ข้อจำกัดที่ควรรู้

1. **GitHub Actions cron ต่ำสุดจริงคือ ~5 นาที** (และอาจดีเลย์เพิ่มอีก 2-10 นาที) ไม่ใช่ 1 นาทีเป๊ะ ดังนั้นแท่ง M1
ที่ตรวจพบสัญญาณอาจปิดไปแล้วสักพักก่อนบอทจะรันรอบถัดไปมาเจอ — เหมาะกับการ "แจ้งเตือนโมเมนตัม" มากกว่าการเข้าไม้ทันทีแบบ HFT
2. **ข้อมูลจาก yfinance ไม่ใช่ real-time tick data จริง** อาจมี delay หรือช่วงข้อมูลขาดหาย
3. **นี่คือเครื่องมือช่วยหาโอกาส ไม่ใช่คำแนะนำการลงทุน** สัญญาณหลอกเกิดขึ้นได้เสมอแม้เงื่อนไขจะเข้มกว่าเดิม
ควรใช้ร่วมกับการบริหารความเสี่ยงของคุณเอง (stop loss, money management)
