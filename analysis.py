"""
ฟังก์ชันวิเคราะห์ทางเทคนิค:
- calc_atr: คำนวณ Average True Range
- has_price_action_d1: เช็คว่า D1 มีการเคลื่อนไหวราคาที่ชัดเจนทั้งขาขึ้นและขาลง
- detect_sideway_box: เช็คว่า H1 อยู่ในกรอบ sideway และคืนขอบบน/ล่างของกรอบ
- check_breakout: เช็คว่าราคาปัจจุบันหลุดกรอบหรือยัง
- detect_sudden_move_d1: เช็คว่าแท่ง D1 ล่าสุดเคลื่อนไหวรุนแรงผิดปกติหรือไม่
"""
import pandas as pd


def calc_atr(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period).mean()


def has_price_action_d1(df_d1, lookback=20, min_atr_pct=0.003, swing_min_ratio=1.5):
    """
    เช็คว่า D1 มี "ขาขึ้น" และ "ขาลง" ที่มีขนาดใหญ่พอ (>= swing_min_ratio * ATR) ภายใน lookback แท่งล่าสุด
    ใช้หลักการเดียวกับโจทย์ max profit / max drawdown:
    - max_up  = ส่วนต่างขาขึ้นที่ใหญ่ที่สุด (จาก low ก่อนหน้า ไป high หลังจากนั้น)
    - max_down = ส่วนต่างขาลงที่ใหญ่ที่สุด (จาก high ก่อนหน้า ไป low หลังจากนั้น)
    """
    if len(df_d1) < lookback + 15:
        return False, {}

    atr_series = calc_atr(df_d1, 14)
    atr = atr_series.iloc[-1]
    last_close = df_d1["Close"].iloc[-1]

    if pd.isna(atr) or last_close == 0:
        return False, {}

    atr_pct = atr / last_close
    if atr_pct < min_atr_pct:
        return False, {"reason": "ATR ต่ำเกินไป ตลาดนิ่ง", "atr_pct": float(atr_pct)}

    window = df_d1.tail(lookback)
    highs = window["High"].values
    lows = window["Low"].values
    n = len(window)

    running_min = lows[0]
    max_up = 0.0
    for i in range(1, n):
        if highs[i] - running_min > max_up:
            max_up = highs[i] - running_min
        if lows[i] < running_min:
            running_min = lows[i]

    running_max = highs[0]
    max_down = 0.0
    for i in range(1, n):
        if running_max - lows[i] > max_down:
            max_down = running_max - lows[i]
        if highs[i] > running_max:
            running_max = highs[i]

    has_up = max_up >= swing_min_ratio * atr
    has_down = max_down >= swing_min_ratio * atr

    info = {
        "atr": float(atr),
        "atr_pct": float(atr_pct),
        "max_up": float(max_up),
        "max_down": float(max_down),
    }
    return (has_up and has_down), info


def detect_sideway_box(df_h1, lookback=20, max_range_atr_ratio=2.5):
    """
    หากรอบ sideway บน H1: ใช้ high สูงสุด / low ต่ำสุด ของ lookback แท่งล่าสุด
    ถือว่า sideway ถ้าความกว้างกรอบ <= max_range_atr_ratio * ATR(H1)
    """
    if len(df_h1) < lookback + 15:
        return False, None, None, None

    atr_series = calc_atr(df_h1, 14)
    atr_h1 = atr_series.iloc[-1]
    if pd.isna(atr_h1) or atr_h1 == 0:
        return False, None, None, None

    window = df_h1.tail(lookback)
    box_high = window["High"].max()
    box_low = window["Low"].min()
    box_range = box_high - box_low

    is_sideway = box_range <= max_range_atr_ratio * atr_h1
    return is_sideway, float(box_high), float(box_low), float(atr_h1)


def check_breakout(latest_price, box_high, box_low, buffer_atr_ratio, atr_h1):
    buffer = buffer_atr_ratio * atr_h1
    if latest_price > box_high + buffer:
        return "UP"
    if latest_price < box_low - buffer:
        return "DOWN"
    return None


def detect_sudden_move_d1(df_d1, atr_period=14, move_threshold_atr=2.0):
    """
    เช็คว่าแท่ง D1 ล่าสุด (วันนี้) มี range ใหญ่ผิดปกติเทียบ ATR ของแท่งก่อนหน้าหรือไม่
    """
    if len(df_d1) < atr_period + 2:
        return False, None, 0.0, 0.0

    atr_series = calc_atr(df_d1, atr_period)
    atr = atr_series.iloc[-2]  # ใช้ ATR ก่อนแท่งปัจจุบัน กันไม่ให้แท่งปัจจุบันไปดันค่า ATR เอง
    if pd.isna(atr) or atr == 0:
        return False, None, 0.0, 0.0

    today = df_d1.iloc[-1]
    today_range = float(today["High"] - today["Low"])
    direction = "UP" if today["Close"] >= today["Open"] else "DOWN"

    is_sudden = today_range >= move_threshold_atr * atr
    return is_sudden, direction, today_range, float(atr)
