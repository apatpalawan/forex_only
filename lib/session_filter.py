"""
Session filter - เทรด M1 เฉพาะช่วงสภาพคล่องสูงเท่านั้น (London / London-NY overlap)
กัน false signal จากช่วงตลาดเบาบาง (เอเชียดึก, ก่อน/หลังตลาดปิด)
"""

from datetime import datetime, timezone
import config


def in_trading_session(now_utc: datetime | None = None) -> bool:
    if not config.SESSION_FILTER_ENABLED:
        return True
    now_utc = now_utc or datetime.now(timezone.utc)
    hour = now_utc.hour
    return config.SESSION_START_UTC <= hour < config.SESSION_END_UTC
