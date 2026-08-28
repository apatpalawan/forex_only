"""
ทดสอบ logic ด้วยข้อมูลจำลอง (ไม่ต่อ network) ก่อนรันจริง
รัน: python test_local.py
"""

import numpy as np
import pandas as pd
from lib.strategy import evaluate_symbol


def make_trend_candles(n, start, step, interval_minutes, noise=0.02, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-01", periods=n, freq=f"{interval_minutes}min")
    close = start + np.cumsum(np.full(n, step)) + rng.normal(0, noise, n)
    open_ = close - step + rng.normal(0, noise, n)
    high = np.maximum(open_, close) + abs(rng.normal(0, noise, n))
    low = np.minimum(open_, close) - abs(rng.normal(0, noise, n))
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close,
                          "Volume": rng.integers(100, 1000, n)}, index=idx)


def make_pullback_then_breakout_m1(n, base, breakout_at, direction, interval_minutes=1, seed=2):
    """M1: เดินขึ้น/ลงเล็กน้อยจนถึงจุด breakout_at แล้วพุ่งทะลุจริง"""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-05", periods=n, freq=f"{interval_minutes}min")
    close = np.full(n, base) + rng.normal(0, 0.01, n)
    sign = 1 if direction == "up" else -1
    for i in range(breakout_at, n):
        close[i] = base + sign * 0.05 * (i - breakout_at + 1)
    open_ = np.roll(close, 1)
    open_[0] = base
    high = np.maximum(open_, close) + 0.005
    low = np.minimum(open_, close) - 0.005
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close,
                          "Volume": rng.integers(100, 1000, n)}, index=idx)


def test_uptrend_triggers():
    # D1: ขาขึ้นชัดเจน (เร่งความชันช่วงท้ายเล็กน้อยให้ MACD > Signal จริง)
    d1_n = 120
    df_d1 = make_trend_candles(d1_n, start=1.0500, step=0.0008, interval_minutes=60 * 24)
    d1_accel = np.linspace(0.0008, 0.0025, 15)
    for i, s in enumerate(d1_accel):
        pos = d1_n - 15 + i
        df_d1.iloc[pos, df_d1.columns.get_loc("Close")] = df_d1["Close"].iloc[pos - 1] + s
        df_d1.iloc[pos, df_d1.columns.get_loc("High")] = df_d1["Close"].iloc[pos] + 0.0005
        df_d1.iloc[pos, df_d1.columns.get_loc("Low")] = df_d1["Close"].iloc[pos] - 0.0002
    # H1: ADX สูง, DI+ > DI-, ATR ขยาย (จำลองด้วยเทรนด์แรงต่อเนื่อง + เร่งท้าย)
    h1_n = 200
    h1 = make_trend_candles(h1_n, start=1.0500, step=0.0004, interval_minutes=60, noise=0.0003)
    # เร่งความชันช่วงท้ายให้ ADX เพิ่มขึ้นจริงและ ATR ratio > 1
    accel = np.linspace(0.0004, 0.0020, 30)
    for i, s in enumerate(accel):
        pos = h1_n - 30 + i
        h1.iloc[pos, h1.columns.get_loc("Close")] = h1["Close"].iloc[pos - 1] + s
        h1.iloc[pos, h1.columns.get_loc("High")] = h1["Close"].iloc[pos] + 0.0005
        h1.iloc[pos, h1.columns.get_loc("Low")] = h1["Close"].iloc[pos] - 0.0002

    # M15: ย่อลงมาใกล้ EMA20 แล้วมีแท่งกลับตัวขึ้น
    m15_n = 60
    m15 = make_trend_candles(m15_n, start=h1["Close"].iloc[-1] - 0.002, step=0.00005, interval_minutes=15, noise=0.0002)
    # บังคับแท่งท้าย ๆ ให้เป็น pullback แล้ว reversal ชัด
    m15.iloc[-2, m15.columns.get_loc("Open")] = m15["Close"].iloc[-3]
    m15.iloc[-2, m15.columns.get_loc("Close")] = m15["Close"].iloc[-3] - 0.001  # แท่งแดง (ย่อ)
    m15.iloc[-1, m15.columns.get_loc("Open")] = m15["Close"].iloc[-2]
    m15.iloc[-1, m15.columns.get_loc("Close")] = m15["Close"].iloc[-2] + 0.0015  # แท่งเขียว (reversal)
    m15.iloc[-1, m15.columns.get_loc("High")] = m15["Close"].iloc[-1] + 0.0002
    m15.iloc[-1, m15.columns.get_loc("Low")] = min(m15["Open"].iloc[-1], m15["Close"].iloc[-2]) - 0.0002

    zone_time = m15.index[-1]
    zone_high = float(m15["High"].iloc[-1])

    # ต่อแท่ง D1/H1/M15 ท้ายสุดอีก 1 แท่ง (ยังไม่ปิด) เพื่อจำลองว่า evaluate_symbol
    # จะตัดมันทิ้งเสมอ - แท่งที่ตั้งใจให้ trigger (ด้านบน) ต้องกลายเป็น "แท่งปิดล่าสุด" แทน
    def _append_unclosed(df, freq):
        extra = pd.DataFrame({
            "Open": [df["Close"].iloc[-1]], "High": [df["Close"].iloc[-1] + 0.0001],
            "Low": [df["Close"].iloc[-1] - 0.0001], "Close": [df["Close"].iloc[-1]],
            "Volume": [500],
        }, index=[df.index[-1] + pd.Timedelta(freq)])
        return pd.concat([df, extra])

    df_d1 = _append_unclosed(df_d1, "1D")
    h1 = _append_unclosed(h1, "1h")
    m15 = _append_unclosed(m15, "15min")

    # M1: หลังโซนแล้วมีแท่งทะลุ high จริง
    m1_n = 20
    m1 = pd.DataFrame({
        "Open": np.full(m1_n, zone_high - 0.0005),
        "High": np.full(m1_n, zone_high - 0.0002),
        "Low": np.full(m1_n, zone_high - 0.0008),
        "Close": np.full(m1_n, zone_high - 0.0003),
        "Volume": np.full(m1_n, 500),
    }, index=pd.date_range(zone_time + pd.Timedelta(minutes=1), periods=m1_n, freq="1min"))
    # แท่งที่ 10 ทะลุ high ของโซนจริง (ปิดเหนือ)
    m1.iloc[10, m1.columns.get_loc("Close")] = zone_high + 0.0010
    m1.iloc[10, m1.columns.get_loc("High")] = zone_high + 0.0015
    # เติมแท่งเผื่อท้าย (ยังไม่ปิด) ให้ evaluate_symbol ตัดแท่งสุดท้ายทิ้งได้โดยไม่กระทบ trigger
    extra = pd.DataFrame({"Open": [m1["Close"].iloc[-1]], "High": [m1["Close"].iloc[-1] + 0.0002],
                           "Low": [m1["Close"].iloc[-1] - 0.0002], "Close": [m1["Close"].iloc[-1]],
                           "Volume": [500]}, index=[m1.index[-1] + pd.Timedelta(minutes=1)])
    m1 = pd.concat([m1, extra])

    result = evaluate_symbol("TESTUP", {"D1": df_d1, "H1": h1, "M15": m15, "M1": m1})
    print("uptrend test result:", result)
    assert result is not None, "ควรเจอ signal บนข้อมูลขาขึ้นที่ตั้งใจให้ trigger"
    assert result["direction"] == "up"
    print("✅ test_uptrend_triggers PASSED")


def test_flat_market_no_signal():
    n_d1 = 120
    idx_d1 = pd.date_range("2026-01-01", periods=n_d1, freq="1D")
    rng = np.random.default_rng(3)
    close = 1.05 + rng.normal(0, 0.0005, n_d1)
    df_d1 = pd.DataFrame({"Open": close, "High": close + 0.0003, "Low": close - 0.0003,
                           "Close": close, "Volume": 500}, index=idx_d1)

    h1 = df_d1.copy()
    h1.index = pd.date_range("2026-01-01", periods=n_d1, freq="1h")

    m15_n = 60
    idx_m15 = pd.date_range("2026-01-05", periods=m15_n, freq="15min")
    close15 = 1.05 + rng.normal(0, 0.0003, m15_n)
    m15 = pd.DataFrame({"Open": close15, "High": close15 + 0.0002, "Low": close15 - 0.0002,
                         "Close": close15, "Volume": 500}, index=idx_m15)

    m1_n = 30
    idx_m1 = pd.date_range("2026-01-05", periods=m1_n, freq="1min")
    close1 = 1.05 + rng.normal(0, 0.0001, m1_n)
    m1 = pd.DataFrame({"Open": close1, "High": close1 + 0.0001, "Low": close1 - 0.0001,
                        "Close": close1, "Volume": 500}, index=idx_m1)

    result = evaluate_symbol("TESTFLAT", {"D1": df_d1, "H1": h1, "M15": m15, "M1": m1})
    print("flat market test result:", result)
    assert result is None, "ตลาด sideway ไม่ควรมี signal"
    print("✅ test_flat_market_no_signal PASSED")


if __name__ == "__main__":
    test_uptrend_triggers()
    test_flat_market_no_signal()
    print("\nALL TESTS PASSED")
