"""
ทดสอบ logic ทั้งหมดแบบ offline ด้วยข้อมูลสังเคราะห์ (ไม่ต้องต่อเน็ต ไม่ต้องมี LINE token)
รัน: python test_local.py
"""
import numpy as np
import pandas as pd

from lib import indicators as ind
from lib import strategy, state_manager

passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")


class Cfg:
    EMA_TREND_FAST = 100
    EMA_TREND_SLOW = 300
    TREND_CROSS_LOOKBACK_BARS = 300
    EMA_SIGNAL_FAST = 9
    EMA_SIGNAL_SLOW = 25
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    RSI_PERIOD = 14
    RSI_MID = 50
    ADX_PERIOD = 14
    ADX_MIN = 20


def make_df_from_closes(closes, noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    closes = np.array(closes, dtype=float)
    n = len(closes)
    high = closes + np.abs(rng.normal(0, noise, n)) + 0.001
    low = closes - np.abs(rng.normal(0, noise, n)) - 0.001
    open_ = closes + rng.normal(0, noise, n) * 0.3
    idx = pd.date_range("2026-01-01", periods=n, freq="1min")
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": closes, "Volume": 100},
        index=idx,
    )


def uptrend_series(n, start=100.0, drift=0.02, noise=0.05, seed=1):
    rng = np.random.default_rng(seed)
    steps = drift + rng.normal(0, noise, n)
    return start + np.cumsum(steps)


def downtrend_series(n, start=200.0, drift=-0.02, noise=0.05, seed=2):
    rng = np.random.default_rng(seed)
    steps = drift + rng.normal(0, noise, n)
    return start + np.cumsum(steps)


def flat_series(n, level=100.0, noise=0.01, seed=3):
    rng = np.random.default_rng(seed)
    return level + rng.normal(0, noise, n)


print("== 1. Indicator sanity ==")

closes = pd.Series(uptrend_series(400, seed=10))
e = ind.ema(closes, 20)
check("ema: matches pandas ewm reference", np.isclose(e.iloc[-1], closes.ewm(span=20, adjust=False, min_periods=20).mean().iloc[-1]))
check("ema: NaN before min_periods", pd.isna(e.iloc[5]))

macd_line, macd_signal, hist = ind.macd(closes, 12, 26, 9)
check("macd: hist == macd_line - signal_line", np.isclose(hist.iloc[-1], macd_line.iloc[-1] - macd_signal.iloc[-1]))
check("macd: positive on strong uptrend", macd_line.iloc[-1] > 0)

up_closes = pd.Series(uptrend_series(60, drift=0.5, noise=0.0, seed=11))
r_up = ind.rsi(up_closes, 14)
check("rsi: near 100 on pure monotonic uptrend (no down-ticks)", r_up.iloc[-1] > 95)

down_closes = pd.Series(downtrend_series(60, drift=-0.5, noise=0.0, seed=12))
r_down = ind.rsi(down_closes, 14)
check("rsi: near 0 on pure monotonic downtrend (no up-ticks)", r_down.iloc[-1] < 5)

flat_closes = pd.Series([100.0] * 60)
r_flat = ind.rsi(flat_closes, 14)
check("rsi: 50 on perfectly flat series (no gain, no loss)", np.isclose(r_flat.iloc[-1], 50.0))

df_up = make_df_from_closes(uptrend_series(200, drift=0.3, noise=0.1, seed=13), noise=0.05, seed=13)
adx_up, pdi_up, mdi_up = ind.adx_di(df_up, 14)
check("adx_di: +DI > -DI in clear uptrend", pdi_up.iloc[-1] > mdi_up.iloc[-1])
check("adx_di: ADX rises above 20 in a clear trending move", adx_up.iloc[-1] > 20)

df_down = make_df_from_closes(downtrend_series(200, drift=-0.3, noise=0.1, seed=14), noise=0.05, seed=14)
adx_down, pdi_down, mdi_down = ind.adx_di(df_down, 14)
check("adx_di: -DI > +DI in clear downtrend", mdi_down.iloc[-1] > pdi_down.iloc[-1])


print("\n== 2. Trend cross detection (_trend_direction) ==")

# สร้างราคา: 400 แท่งขาลงก่อน (EMA100 ต่ำกว่า EMA300) แล้วสลับเป็นขาขึ้นแรงๆ ต่ออีก 500 แท่ง
# ให้เกิดจุดตัด EMA100 ขึ้นเหนือ EMA300 อย่างชัดเจนระหว่างทาง
part1 = downtrend_series(400, start=200, drift=-0.05, noise=0.02, seed=20)
part2 = uptrend_series(500, start=part1[-1], drift=0.15, noise=0.02, seed=21)
closes_cross_up = pd.Series(np.concatenate([part1, part2]))

ema100 = ind.ema(closes_cross_up, 100)
ema300 = ind.ema(closes_cross_up, 300)
# ใช้ lookback ที่กว้างพอจะครอบคลุมจุดตัดจริง (คร่าวๆ อยู่แถวบาร์ 400-500 นับจากต้น
# หรือประมาณ 400-500 บาร์ก่อนบาร์สุดท้ายจากทั้งหมด 900 บาร์)
trend, cross_idx = strategy._trend_direction(ema100, ema300, lookback=600)
check("trend_direction: detects 'up' after a real EMA100x300 cross-up", trend == "up")
check("trend_direction: cross_idx is not None when cross found within lookback", cross_idx is not None)

part3 = uptrend_series(400, start=100, drift=0.05, noise=0.02, seed=22)
part4 = downtrend_series(500, start=part3[-1], drift=-0.15, noise=0.02, seed=23)
closes_cross_down = pd.Series(np.concatenate([part3, part4]))
ema100d = ind.ema(closes_cross_down, 100)
ema300d = ind.ema(closes_cross_down, 300)
trend_d, cross_idx_d = strategy._trend_direction(ema100d, ema300d, lookback=300)
check("trend_direction: detects 'down' after a real EMA100x300 cross-down", trend_d == "down")

# ไม่มีจุดตัดในช่วง lookback -> fallback ใช้ทิศทางปัจจุบัน
long_up = pd.Series(uptrend_series(1000, drift=0.05, noise=0.02, seed=24))
ema100f = ind.ema(long_up, 100)
ema300f = ind.ema(long_up, 300)
trend_f, cross_idx_f = strategy._trend_direction(ema100f, ema300f, lookback=50)
check("trend_direction: fallback to current relationship when no cross within lookback", trend_f == "up" and cross_idx_f is None)


print("\n== 3. Full evaluate() — BUY scenario ==")
# เทรนด์ขึ้นชัดเจนต่อเนื่องยาวพอ (EMA100>EMA300, EMA9>EMA25, RSI>50, MACD>signal, ADX/DI ฝั่งขึ้น)
buy_closes = uptrend_series(900, start=100, drift=0.08, noise=0.04, seed=30)
df_buy = make_df_from_closes(buy_closes, noise=0.03, seed=30)
res_buy = strategy.evaluate(df_buy, Cfg)
check("evaluate: BUY signal fires on strong sustained uptrend", res_buy["signal"] == "buy")
check("evaluate: BUY details report trend=up", res_buy["details"].get("trend") == "up")

print("\n== 4. Full evaluate() — SELL scenario ==")
sell_closes = downtrend_series(900, start=200, drift=-0.08, noise=0.04, seed=31)
df_sell = make_df_from_closes(sell_closes, noise=0.03, seed=31)
res_sell = strategy.evaluate(df_sell, Cfg)
check("evaluate: SELL signal fires on strong sustained downtrend", res_sell["signal"] == "sell")

print("\n== 5. Full evaluate() — no signal scenarios ==")
flat_closes_long = flat_series(900, level=100, noise=0.01, seed=32)
df_flat = make_df_from_closes(flat_closes_long, noise=0.01, seed=32)
res_flat = strategy.evaluate(df_flat, Cfg)
check("evaluate: flat/sideway market -> no signal", res_flat["signal"] is None)

df_short = make_df_from_closes(uptrend_series(50, seed=33), noise=0.02, seed=33)
res_short = strategy.evaluate(df_short, Cfg)
check("evaluate: not enough bars for EMA300 warm-up -> no signal (not_enough_data)", res_short["signal"] is None and res_short["reason"] == "not_enough_data")

# เทรนด์ขึ้น แต่ EMA9/25 ยังไม่เรียงตัวตาม (จำลองโดยหักมุมราคาลงแรงช่วงท้ายชั่วครู่)
mixed_up = uptrend_series(900, start=100, drift=0.08, noise=0.03, seed=34)
mixed_up_tail_down = downtrend_series(15, start=mixed_up[-1], drift=-0.6, noise=0.02, seed=35)
mixed_closes = np.concatenate([mixed_up, mixed_up_tail_down])
df_mixed = make_df_from_closes(mixed_closes, noise=0.03, seed=34)
res_mixed = strategy.evaluate(df_mixed, Cfg)
check("evaluate: uptrend regime but EMA9 dipped below EMA25 -> no buy signal", res_mixed["signal"] != "buy")


print("\n== 6. State manager (dedup logic) ==")
state = {}
check("should_alert: first buy signal -> alert", state_manager.should_alert(state, "EURUSD", "buy") is True)
state_manager.update_state(state, "EURUSD", "buy")
check("should_alert: same buy signal again -> no alert (dedup)", state_manager.should_alert(state, "EURUSD", "buy") is False)
state_manager.update_state(state, "EURUSD", None)
check("should_alert: signal drops to None -> no alert (None never alerts)", state_manager.should_alert(state, "EURUSD", None) is False)
check("should_alert: buy comes back after None -> alert again", state_manager.should_alert(state, "EURUSD", "buy") is True)
state_manager.update_state(state, "EURUSD", "buy")
check("should_alert: flips from buy to sell -> alert", state_manager.should_alert(state, "EURUSD", "sell") is True)
check("should_alert: brand-new symbol with no prior state -> alert on first signal", state_manager.should_alert(state, "GBPUSD", "sell") is True)


print(f"\n{'='*40}\nTOTAL: {passed} passed, {failed} failed\n{'='*40}")
if failed:
    raise SystemExit(1)
