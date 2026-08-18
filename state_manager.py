"""
state_manager.py
Tiny JSON state file so a breakout on a given H1 candle is only alerted
once - even though the scan runs every 30 minutes and the same "latest
closed H1 candle" is seen twice per hour before it rolls over.

Committed back to the repo by the GitHub Actions workflow after each run.
"""

import json
import os
import config


def load_state() -> dict:
    if not os.path.exists(config.STATE_PATH):
        return {}
    try:
        with open(config.STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[state_manager] failed to read {config.STATE_PATH}, starting fresh: {e}")
        return {}


def save_state(state: dict) -> None:
    with open(config.STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, default=str)
