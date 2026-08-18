# Forex + Gold H1 Sideway-Breakout Radar Bot

ส่งเข้า LINE OA **เฉพาะตอนที่ H1 breakout ออกจากช่วง sideway (consolidation) เท่านั้น**

## หลักการทำงาน

1. ดูแท่ง H1 ที่ปิดแล้ว 15 แท่งก่อนหน้าแท่งล่าสุด (`SIDEWAY_LOOKBACK`) — ถ้าช่วง high-low ของ 15 แท่งนี้ "แคบ" เทียบกับความผันผวนเฉลี่ย (ATR) → ถือว่าเป็นช่วง **sideway**
2. ถ้าแท่งล่าสุดที่ปิดแล้ว **breakout ทะลุกรอบ sideway นั้น** (ปิดสูงกว่าขอบบน หรือต่ำกว่าขอบล่าง) → ถือว่าเป็น **breakout**
3. ผ่านทั้ง 2 เงื่อนไข → ส่งเข้า LINE
4. มี `state.json` เก็บว่าแท่งไหนแจ้งไปแล้ว (commit กลับเข้า repo อัตโนมัติหลังทุกรอบ) เพื่อไม่ให้แจ้งซ้ำแท่งเดิม 2 รอบ (เพราะสแกนทุก 30 นาที แต่แท่ง H1 ปิดทุก 1 ชม. เลยมีบางแท่งที่ถูกสแกนซ้ำ 2 รอบก่อนแท่งใหม่จะมา)

## ปรับความไวของสัญญาณได้ที่ `config.py`

- `SIDEWAY_LOOKBACK` (ค่าเริ่มต้น 15) — จำนวนแท่งที่ใช้กำหนดกรอบ sideway ยิ่งมากยิ่งมองภาพกว้างขึ้น
- `ATR_PERIOD` (ค่าเริ่มต้น 14) — คาบคำนวณ ATR มาตรฐาน
- `ATR_MULTIPLIER` (ค่าเริ่มต้น 5.0) — ยิ่งค่าน้อย ยิ่งเข้มงวด (ต้องแคบมากถึงนับเป็น sideway) ยิ่งค่ามาก ยิ่งได้สัญญาณบ่อยขึ้นแต่คุณภาพอาจลดลง — ค่านี้ปรับจากการทดสอบจำลองสถานการณ์ตลาดจริง (ช่วง 15 แท่งมักกว้างกว่า ATR ของแท่งเดียวราวๆ 3-4.5 เท่า)

## โครงสร้างไฟล์

```
config.py             คู่เงินที่สแกน, ค่า sideway/breakout, LINE env vars
market_data.py         ดึง H1 candles จาก yfinance
price_action.py         ตรวจ sideway + breakout บนแท่งที่ปิดแล้วเท่านั้น
state_manager.py        อ่าน/เขียน state.json (กันแจ้งซ้ำ)
line_notify.py           format ข้อความ + push เข้า LINE Messaging API
main.py                   orchestrate: scan ทุกคู่เงิน -> ส่ง LINE -> เซฟ state
state.json                เก็บแท่งล่าสุดที่แจ้งไปแล้วต่อคู่เงิน (เริ่มต้นว่างเปล่า)
requirements.txt
.github/workflows/sideway-breakout.yml   cron ทุก 30 นาที + commit state.json กลับ
```

## ตั้งค่า GitHub Secrets (ใช้ของเดิมที่มีอยู่แล้วได้เลย)

- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_TARGET_IDS` (comma-separated user/group ids)

## ทดสอบก่อนใช้จริง

```
pip install -r requirements.txt
export LINE_CHANNEL_ACCESS_TOKEN="your-token"
export LINE_TARGET_IDS="your-line-id"
python main.py
```

หลัง push ขึ้น GitHub แนะนำให้กด **Run workflow** (workflow_dispatch) ทดสอบยิงจริงก่อนปล่อยรันตาม schedule — เช็ค log ว่าไม่ error และดูว่า `state.json` ถูก commit กลับเข้า repo หลังรันเสร็จ (สังเกตจาก step "Commit updated state.json" ใน log)
