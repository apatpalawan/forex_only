"""
Forex + Gold H1 Sideway-Breakout Radar Bot - Config
Alert only when H1 breaks out of a tight (sideway) range.
"""

import os

# ---------------------------------------------------------------------------
# Symbols: display name -> Yahoo Finance ticker
# ---------------------------------------------------------------------------
SYMBOLS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "USDCHF": "USDCHF=X",
    "USDCAD": "USDCAD=X",
    "AUDUSD": "AUDUSD=X",
    "NZDUSD": "NZDUSD=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
    "XAUUSD": "XAUUSD=X",   # if this ticker misbehaves on yfinance, try "GC=F" instead
}

# ---------------------------------------------------------------------------
# H1 data window
# ---------------------------------------------------------------------------
H1_PERIOD = "1mo"
H1_INTERVAL = "1h"

# ---------------------------------------------------------------------------
# Sideway / breakout settings
# ---------------------------------------------------------------------------
# Number of closed H1 candles used to define the "sideway" range (right before
# the candle being checked for a breakout).
SIDEWAY_LOOKBACK = 15

# ATR period (Average True Range) used as the volatility yardstick.
ATR_PERIOD = 14

# The sideway range (high-low over SIDEWAY_LOOKBACK candles) must be <= this
# many times the ATR to count as "tight / sideway". Lower = stricter (needs a
# tighter range to qualify). Raise this if you want more signals, lower it if
# you want fewer / higher-quality ones. Calibrated against simulated H1
# ranging behavior (15-candle range typically runs ~3-4.5x the single-candle
# ATR) - 4.5 catches most genuine consolidation while still excluding clearly
# trending periods (which run much higher).
ATR_MULTIPLIER = 5.0

# ---------------------------------------------------------------------------
# LINE Messaging API (GitHub Actions secrets already set on the repo)
# ---------------------------------------------------------------------------
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_TARGET_IDS = os.environ.get("LINE_TARGET_IDS", "")  # comma-separated user/group ids

# ---------------------------------------------------------------------------
# State file (remembers the last alerted breakout candle per symbol, so the
# same breakout isn't sent twice while the H1 candle is still the "latest
# closed" one across multiple 30-min scans)
# ---------------------------------------------------------------------------
STATE_PATH = "state.json"

# Retry/network settings for yfinance fetches
FETCH_MAX_RETRIES = 3
FETCH_RETRY_DELAY_SEC = 2.0
