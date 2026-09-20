# Forex/Gold M1 EMA Trigger Bot → แจ้งเตือนเข้า LINE OA

บอทสแกนคู่เงินยอดนิยม + ทองคำ บน **timeframe M1** ทุก 5 นาที ด้วยเงื่อนไข:

**ขาขึ้น (Buy)**
1. EMA100 ตัด EMA300 ขึ้น (เทรนด์หลัก, ต้องเกิดก่อนเสมอ)
2. หลังจากนั้น EMA9 ต้องเรียงตัวอยู่ **เหนือ** EMA25 (เช็คสถานะปัจจุบัน)
3. ยืนยันด้วย MACD (macd line > signal line), RSI(14) > 50, ADX ≥ 20 และ +DI > -DI

**ขาลง (Sell)** — ตรงข้ามทั้งหมด (EMA100 ตัด EMA300 ลง → EMA9 อยู่ใต้ EMA25 → MACD/RSI/ADX ฝั่งลง)

เมื่อครบทุกเงื่อนไข บอทจะส่งข้อความสั้นๆ เข้า LINE (เช่น `🟢 Buy EURUSD (M1)`) และจะไม่แจ้งซ้ำสัญญาณเดิมทุก
5 นาที — แจ้งใหม่ก็ต่อเมื่อสัญญาณเปลี่ยน (buy → sell, หรือหายไปแล้วกลับมาใหม่)

## โครงสร้างไฟล์

```
config.py                 พารามิเตอร์ทั้งหมด (คู่เงิน, EMA/MACD/RSI/ADX) — ปรับได้ตรงนี้
lib/indicators.py          EMA, MACD, RSI, ADX/DI (คำนวณเองด้วย pandas ไม่พึ่ง TA-lib)
lib/data_fetcher.py        ดึงราคา M1 จาก Yahoo Finance (yfinance + curl_cffi กัน rate-limit)
lib/strategy.py            logic หลัก: หาจุดตัด EMA100/300 → เช็ค EMA9/25 → ยืนยัน MACD/RSI/ADX
lib/state_manager.py       อ่าน/บันทึก state.json (กันแจ้งเตือนซ้ำสัญญาณเดิม)
lib/line_notify.py         ส่งข้อความเข้า LINE (push ถ้ามี LINE_TARGET_IDS, ไม่งั้น broadcast)
main.py                     สแกนทุก symbol แล้วส่งแจ้งเตือน
test_local.py               ทดสอบทั้งหมดแบบ offline ด้วยข้อมูลสังเคราะห์ (รันก่อน push ทุกครั้ง)
state.json                  เก็บสัญญาณล่าสุดต่อ symbol (bot commit กลับ repo เองอัตโนมัติ)
.github/workflows/m1_trigger.yml   รันทุก 5 นาที
```

## หมายเหตุสำคัญเรื่องทองคำ

`XAUUSD=X` ไม่มีข้อมูล M1 บน Yahoo Finance (คืน HTTP 404) จึงตั้งค่าให้ `config.py` ดึงข้อมูลจาก
`GC=F` (COMEX gold futures) แทน แต่ยังคงแสดงผลในข้อความ LINE เป็น "XAUUSD" ตามปกติ

## ขั้นตอนติดตั้ง

### 1. ตั้งค่า GitHub Secrets

ไปที่ repo → **Settings → Secrets and variables → Actions**
ใช้ secret เดิมที่มีอยู่แล้วได้เลย ไม่ต้องสร้างใหม่:

| Name                        | Value                          |
| --------------------------- | ------------------------------ |
| `LINE_CHANNEL_ACCESS_TOKEN` | token จาก LINE Developers Console |
| `LINE_TARGET_IDS`           | (ไม่บังคับ) user id คั่นด้วย comma |

### 2. ทดสอบในเครื่องก่อน (ตามที่เคยขอไว้เสมอ — ทดลองก่อนรันจริง)

```
pip install -r requirements.txt
python test_local.py      # ต้องผ่านทั้งหมดก่อน push
python main.py             # ทดสอบดึงข้อมูลจริง ถ้าไม่ตั้ง LINE token จะ print แทนการส่งจริง
```

### 3. Push ขึ้น GitHub แล้วเปิด Actions

เข้าไปที่แท็บ **Actions** ของ repo → workflow "M1 EMA Trigger Scan" → **Run workflow** เพื่อทดสอบรันด้วยมือก่อน
ดู log ว่าดึงข้อมูล/คำนวณ/ส่ง LINE ได้ถูกต้องไหม ก่อนปล่อยให้ cron รันอัตโนมัติทุก 5 นาที

## ปรับพารามิเตอร์

เปิด `config.py` ปรับได้:
- `EMA_TREND_FAST` / `EMA_TREND_SLOW` — EMA คู่หลักที่กำหนดเทรนด์ (ปัจจุบัน 100/300)
- `EMA_SIGNAL_FAST` / `EMA_SIGNAL_SLOW` — EMA คู่สัญญาณ (ปัจจุบัน 9/25)
- `TREND_CROSS_LOOKBACK_BARS` — ย้อนหลังกี่แท่งในการมองหาจุดตัด EMA100/300 ล่าสุด
- `ADX_MIN` — ค่า ADX ขั้นต่ำที่ถือว่าเทรนด์มีแรงพอ
- `RSI_MID` — เส้นกลาง RSI ที่ใช้แบ่งฝั่งขึ้น/ลง (ปกติ 50)

## ข้อจำกัดที่ควรรู้

1. ข้อมูลจาก yfinance/Yahoo Finance ไม่ใช่ real-time tick data จริง อาจมี delay
2. GitHub Actions cron ไม่ตรงเวลาเป๊ะ 100% โดยเฉพาะ repo ที่ไม่ค่อย active
3. เครื่องมือนี้เป็นตัวช่วยหาโอกาส ไม่ใช่คำแนะนำการลงทุน ควรใช้ร่วมกับการบริหารความเสี่ยงเสมอ
