# Forex/Gold Sideway-Breakout Bot → แจ้งเตือนเข้า LINE OA

บอทสแกนหาคู่เงินยอดนิยม + ทองคำ (XAUUSD) ที่:
- **D1** มี price action ชัดเจนทั้งขาขึ้นและขาลง (ไม่ใช่ตลาดนิ่ง)
- **H1** กำลังอยู่ในช่วง sideway (กำลังสร้างกรอบ)

แล้วรอ **breakout** ออกจากกรอบ H1 นั้น เพื่อส่งสัญญาณเข้า LINE Official Account
พร้อมระบบแจ้งเตือนทันทีเมื่อ D1 มีการเคลื่อนไหวรุนแรงกระทันหัน

## โครงสร้างไฟล์

```
config.py                 พารามิเตอร์ทั้งหมด (คู่เงิน, threshold ต่างๆ) — ปรับได้ตรงนี้
data_fetcher.py            ดึงราคาจาก Yahoo Finance (yfinance)
analysis.py                logic วิเคราะห์: ATR, price action, sideway box, breakout, sudden move
line_notify.py              ส่งข้อความเข้า LINE
state_manager.py           อ่าน/บันทึก state.json
main_scan.py                สแกนหลัก รันตามเวลา 08:00/10:00/13:00/15:00/19:00 (เวลาไทย)
breakout_monitor.py         เช็ค breakout รันถี่ทุก 15 นาที
sudden_move_monitor.py      เช็คการเคลื่อนไหวรุนแรงกระทันหันบน D1 รันถี่ทุก 20 นาที
state.json                  เก็บสถานะกรอบ/การแจ้งเตือน (bot จะ commit กลับ repo เองอัตโนมัติ)
.github/workflows/          GitHub Actions 3 ตัว ตามข้างบน
```

## ทำไมต้องมี job รันถี่ (15/20 นาที) เพิ่มจาก 5 รอบ/วัน

การสแกนหา "คู่เงินไหนน่าสนใจ" (D1 price action + H1 sideway) รันแค่ 5 รอบ/วันตามที่ขอได้
แต่การ**รอ breakout**และ**จับการเคลื่อนไหวรุนแรงกระทันหัน**ต้องเช็คถี่กว่านั้นมาก ไม่งั้นจะพลาดจังหวะ
เพราะถ้ารอถึงรอบสแกนถัดไป (เช่นจาก 10:00 ไป 13:00) ราคาอาจ breakout และวิ่งไปแล้วตั้งแต่ 11 โมง
จึงแยกเป็น 3 workflows ตามที่อธิบายด้านบน — คุณปรับความถี่ได้เองใน cron ของแต่ละไฟล์ `.yml`

## ขั้นตอนติดตั้ง

### 1. สร้าง LINE Official Account + เปิด Messaging API

1. ไปที่ [LINE Official Account Manager](https://manager.line.biz/) สร้าง OA (ถ้ายังไม่มี)
2. ไปที่ [LINE Developers Console](https://developers.line.biz/console/) เลือก Provider → เลือก Channel ของ OA นั้น → แท็บ **Messaging API**
3. คัดลอก **Channel access token (long-lived)** — ถ้ายังไม่มีให้กด Issue
4. (ทางเลือก) ถ้าต้องการส่งแบบ push หาตัวเองโดยเฉพาะแทนการ broadcast ให้ทุกคนที่แอด OA:
   - เปิด webhook หรือใช้ LINE Official Account Manager ดู User ID ของตัวเองที่แอดเพื่อนแล้ว
   - หรือปล่อยว่างไว้แล้วใช้ broadcast (ส่งไปหาทุกคนที่แอดเพื่อน OA) ก็ได้ ง่ายกว่า

### 2. อัปโหลดโค้ดขึ้น GitHub

สร้าง repository ใหม่ (private แนะนำ เพราะมี logic การเทรดของคุณ) แล้ว push โค้ดชุดนี้ขึ้นไป

```bash
cd forex-bot
git init
git add .
git commit -m "init forex bot"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

### 3. ตั้งค่า GitHub Secrets

ไปที่ repo → **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | token จากขั้นตอนที่ 1 |
| `LINE_TARGET_IDS` | (ไม่บังคับ) user id คั่นด้วย comma ถ้าต้องการ push เฉพาะคน แทน broadcast |

### 4. เปิดใช้งาน GitHub Actions

ไปที่แท็บ **Actions** ของ repo แล้วกด Enable workflows (ถ้ายังไม่ auto-enable)
เข้าไปที่ workflow แต่ละตัว → **Run workflow** เพื่อทดสอบรันด้วยมือก่อนครั้งแรก จะได้เห็น log ว่าทำงานถูกต้องไหม

### 5. ปรับพารามิเตอร์ตามสไตล์การเทรดของคุณ

เปิด `config.py` ปรับได้เลย เช่น:
- `D1_MIN_ATR_PCT`, `D1_SWING_MIN_RATIO` — ความ "ชัดเจน" ของ price action ที่ต้องการ
- `H1_MAX_RANGE_ATR_RATIO` — กรอบ sideway แคบ/กว้างแค่ไหนถึงจะนับ
- `BREAKOUT_BUFFER_ATR` — กัน false breakout (ยิ่งสูงยิ่งรอ confirm มากขึ้น แต่เข้าช้าลง)
- `SUDDEN_MOVE_ATR_RATIO` — เกณฑ์ความแรงของการเคลื่อนไหวกระทันหัน

## ข้อจำกัดที่ควรรู้

1. **ข้อมูลจาก yfinance/Yahoo Finance ไม่เป็นทางการ** ไม่ใช่ real-time tick data จริง อาจมี delay
   หรือช่วงที่ข้อมูลขาดหาย โดยเฉพาะ gold/forex ticker (`XAUUSD=X` ฯลฯ) — แนะนำให้รัน
   workflow ด้วยมือ (`workflow_dispatch`) ทดสอบดูก่อนว่าดึงข้อมูลได้ปกติจริงในบัญชี GitHub ของคุณ
   ถ้าต้องการความน่าเชื่อถือสูงขึ้นสำหรับใช้เทรดจริง ควรพิจารณาเปลี่ยนไปใช้ API ที่มี key เช่น
   Twelve Data, OANDA, หรือ Polygon.io (โค้ดใน `data_fetcher.py` แก้ให้เรียก API อื่นแทนได้ไม่ยาก)
2. **GitHub Actions cron ไม่ตรงเวลาเป๊ะ 100%** โดยเฉพาะ public repo ที่มีคนใช้เยอะ อาจดีเลย์ได้
   5-15 นาที และ schedule อาจถูก GitHub ข้ามไปบ้างถ้า repo ไม่ active
3. **ระบบนี้เป็นเครื่องมือช่วยหาโอกาส ไม่ใช่คำแนะนำการลงทุน** breakout ปลอมเกิดขึ้นได้เสมอ
   ควรใช้ร่วมกับการบริหารความเสี่ยง (stop loss, money management) ของคุณเอง

## ทดสอบรันในเครื่องตัวเอง (ก่อน deploy)

```bash
pip install -r requirements.txt
export LINE_CHANNEL_ACCESS_TOKEN="your-token"
python main_scan.py
python breakout_monitor.py
python sudden_move_monitor.py
```

ถ้าไม่ตั้ง `LINE_CHANNEL_ACCESS_TOKEN` บอทจะ print ข้อความออกทาง console แทนการส่งจริง
ใช้ debug logic ได้โดยไม่ต้องมี LINE token ก่อนก็ได้
