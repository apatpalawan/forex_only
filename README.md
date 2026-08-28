# M1 Multi-Timeframe Trigger Bot (XAUUSD only) → แจ้งเตือนเข้า LINE OA

บอทสแกน **ทองคำ (XAUUSD) เท่านั้น** ผ่าน 4 ชั้น timeframe ก่อนส่งสัญญาณเข้า LINE:

1. **D1** — หาทิศทางหลัก จาก EMA20/EMA50 + MACD ต้องสอดคล้องกันทั้งคู่ (`up`/`down`) ไม่งั้นข้าม
2. **H1** — ยืนยันความแข็งแรงของเทรนด์: ADX > `ADX_MIN` และต้องเพิ่มขึ้นจากแท่งก่อนหน้า, DI+/DI- ต้องห่างกันพอ (`DI_GAP_MIN`) และสอดคล้องทิศทาง D1, ATR ต้องขยายตัว (`ATR_RATIO_MIN`)
3. **M15** — หาแท่งที่ราคาย่อเข้าใกล้ EMA20(M15) แล้วเกิดแท่งกลับตัว (reversal) ตามทิศทาง D1/H1 → กำหนดเป็น "โซน" (high/low)
4. **M1** — รอแท่ง M1 **ที่ปิดแล้ว** ทะลุ high/low ของโซน M15 นั้นภายใน `M1_CONFIRM_WINDOW_BARS` แท่ง → ถือเป็น trigger เข้าไม้

**ทุก timeframe (D1/H1/M15/M1) จะตัดแท่งสุดท้ายที่ยังไม่ปิดออกก่อนคำนวณเสมอ** (`drop_unclosed_candle` ใน `lib/strategy.py`) กัน repaint ระหว่างแท่งกำลังก่อตัว

ผ่านครบทั้ง 4 ชั้น → ส่งเข้า LINE OA (ข้อความสั้น ประหยัด quota) พร้อม dedupe กันแจ้งซ้ำแท่งเดิม และจำกัดสูงสุด `MAX_ALERTS_PER_SYMBOL_PER_DAY` ครั้ง/วัน

## โครงสร้างไฟล์

```
config.py                 พารามิเตอร์ทั้งหมด (symbol, threshold แต่ละชั้น, session, LINE env vars)
main.py                   orchestrate: เช็ค session -> ดึงราคา -> ประเมินสัญญาณ -> ส่ง LINE -> เซฟ state
lib/data_fetcher.py        ดึง D1/H1/M15/M1 candles จาก yfinance (curl_cffi impersonation + jitter delay กัน rate-limit)
lib/indicators.py          EMA / MACD / ATR / ADX+DI (คำนวณด้วย pandas ล้วน)
lib/strategy.py            logic หลัก D1->H1->M15->M1 รวมถึงตัด unclosed candle ทุก timeframe
lib/session_filter.py      เทรดเฉพาะช่วง London/NY overlap (07-16 UTC ตาม config)
lib/news_filter.py         (ปิดไว้ default) เชื่อม Forex Factory calendar ระงับแจ้งเตือนใกล้ข่าว High impact
lib/state_manager.py       อ่าน/บันทึก state.json (กันแจ้งซ้ำแท่งเดิม + จำกัดจำนวนแจ้งเตือน/วัน)
lib/line_notify.py         format ข้อความสั้น + push เข้า LINE Messaging API
state.json                 เก็บ trigger_time ล่าสุดต่อ symbol (bot commit กลับ repo เองอัตโนมัติ)
test_local.py              ทดสอบ logic ด้วยข้อมูลจำลอง (ไม่ต่อ network) - รันก่อน deploy ทุกครั้ง
.github/workflows/m1_trigger.yml   cron ทุก 5 นาที + commit state.json กลับ
```

## ตั้งค่า GitHub Secrets (ใช้ของเดิมที่มีอยู่แล้วได้เลย)

- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_TARGET_IDS` (comma-separated user/group ids)

## ทดสอบก่อนใช้จริง (ทดลองก่อนรันจริงเสมอ)

```
pip install -r requirements.txt
python test_local.py          # จำลอง logic ด้วยข้อมูลปลอม ไม่ต่อ network เลย
export LINE_CHANNEL_ACCESS_TOKEN="your-token"
export LINE_TARGET_IDS="your-line-id"
python main.py                 # รันจริงครั้งเดียว ต่อ yfinance/LINE จริง
```

หลัง push ขึ้น GitHub แนะนำกด **Run workflow** (workflow_dispatch) ทดสอบยิงจริงก่อนปล่อยรันตาม schedule — เช็ค log ว่าไม่ error และ `state.json` ถูก commit กลับเข้า repo หลังรันเสร็จ

## ปรับพารามิเตอร์ได้ที่ `config.py`

- `EMA_FAST/EMA_SLOW`, `MACD_*` — ความไวของทิศทาง D1
- `ADX_MIN`, `ADX_MUST_RISE`, `DI_GAP_MIN`, `ATR_RATIO_MIN` — ความเข้มงวดของการยืนยัน H1
- `PULLBACK_EMA_TOLERANCE_PCT`, `M15_LOOKBACK_BARS` — ความใกล้ EMA20 และช่วงมองย้อนหลังของ M15
- `M1_CONFIRM_WINDOW_BARS` — รอ breakout บน M1 ได้กี่แท่งก่อนโซนหมดอายุ
- `SESSION_START_UTC/SESSION_END_UTC` — ช่วงเวลาที่ยอมให้เทรด
- `MAX_ALERTS_PER_SYMBOL_PER_DAY` — เพดานแจ้งเตือน/วัน กัน over-alert

## ข้อจำกัดที่ควรรู้

1. ข้อมูลจาก yfinance ไม่ใช่ real-time tick data จริง อาจมี delay หรือช่วงข้อมูลขาดหาย
2. GitHub Actions cron ทุก 5 นาทีจริง ๆ อาจดีเลย์เพิ่ม 2-10 นาทีตามคิว โดยเฉพาะช่วงคนใช้เยอะ
3. เครื่องมือช่วยหาโอกาส ไม่ใช่คำแนะนำการลงทุน ควรใช้ร่วมกับ risk management ของตัวเอง
