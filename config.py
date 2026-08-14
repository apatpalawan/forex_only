"""
Forex + Gold MACD Radar Bot - Config
D1 MACD cross -> H1 MACD cross (same direction, occurring after D1 cross) -> LINE alert
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
# MACD standard settings
# ---------------------------------------------------------------------------
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ---------------------------------------------------------------------------
# Data windows (need enough closed candles to warm up EMA26 + Signal9)
# ---------------------------------------------------------------------------
D1_PERIOD = "6mo"
D1_INTERVAL = "1d"

H1_PERIOD = "1mo"
H1_INTERVAL = "1h"

# ---------------------------------------------------------------------------
# Scan rounds (Thai time) - for logging/labelling only, actual timing is
# controlled by the GitHub Actions cron schedule
# ---------------------------------------------------------------------------
SEND_TIMES_TH = ["09:00", "12:00", "14:00", "16:00", "19:00"]

# ---------------------------------------------------------------------------
# LINE Messaging API (set these as GitHub Actions secrets)
# ---------------------------------------------------------------------------
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_TO = os.environ.get("LINE_TO", "")  # user id / group id / room id to push to

# Retry/network settings for yfinance fetches
FETCH_MAX_RETRIES = 3
FETCH_RETRY_DELAY_SEC = 2.0
