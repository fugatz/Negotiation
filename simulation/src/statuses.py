from __future__ import annotations


BOOKED = "booked"
BOOKED_WITH_MARKET_HEALTH_WARNING = "booked_with_market_health_warning"
NEEDS_SCOPE_CALIBRATION = "needs_scope_calibration"
BOOKED_STATUSES = {BOOKED, BOOKED_WITH_MARKET_HEALTH_WARNING}


def is_booked_status(status: str) -> bool:
    return status in BOOKED_STATUSES
