# Forex + Gold MACD Radar Bot → ส่งเข้า LINE OA

บอทสแกนคู่เงิน major/minor + ทองคำ (XAUUSD) โดยใช้ MACD:

1. ตรวจ **D1** ว่ามี MACD ตัดกันใหม่ในแท่งที่ปิดแล้วหรือไม่ (CROSS UP / CROSS DOWN)
2. ถ้าผ่าน → ตรวจ **H1** ว่ามี MACD ตัดกัน**ทิศทางเดียวกัน**กับ D1 หรือไม่ และต้องเกิด**หลังจาก**การตัดของ D1
3. ผ่านทั้งสองขั้น → ส่งเข้า LINE OA
4. ไม่มี state เก็บข้ามรอบ — ทุกรอบสแกนใหม่หมดอัตโนมัติ (เพราะ GitHub Actions แต่ละ run คือ process ใหม่)

**ส่งเข้า LINE เฉพาะตอนที่เจอ match จริงเท่านั้น** — ถ้ารอบไหนไม่มีคู่เงินผ่านเงื่อนไข จะไม่ส่งข้อความเลย (ประหยัดโควต้า LINE)

## โครงสร้างไฟล์

```
config.py            คู่เงินที่สแกน, ค่า MACD (12,26,9), LINE env vars
market_data.py        ดึง D1/H1 candles จาก yfinance (มี browser-impersonation session กัน rate-limit)
macd_scanner.py        คำนวณ MACD + ตรวจ "cross ใหม่" บนแท่งที่ปิดแล้วเท่านั้น
line_notify.py         format ข้อความ + push เข้า LINE Messaging API
main.py                 orchestrate: D1 scan → H1 confirm → ส่ง LINE
requirements.txt
.github/workflows/forex-macd.yml   cron ทุก 30 นาที ตลอดวัน (24 ชม.)
```

## ตั้งค่า GitHub Secrets

Settings → Secrets and variables → Actions → New repository secret

| Name | ค่า |
| --- | --- |
| `LINE_CHANNEL_ACCESS_TOKEN` | Channel access token จาก LINE Developers Console |
| `LINE_TO` | user id / group id / room id ที่จะ push ข้อความไปหา |

## ทดสอบก่อนใช้จริง

```
pip install -r requirements.txt
export LINE_CHANNEL_ACCESS_TOKEN="your-token"
export LINE_TO="your-line-id"
python main.py
```

หลัง push ขึ้น GitHub แนะนำให้กด **Run workflow** (workflow_dispatch) ทดสอบยิงจริงก่อนปล่อยรันตาม schedule
