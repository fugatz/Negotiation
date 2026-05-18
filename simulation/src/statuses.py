from __future__ import annotations


BOOKED = "booked"
BOOKED_WITH_MARKET_HEALTH_WARNING = "booked_with_market_health_warning"
BOOKED_STATUSES = {BOOKED, BOOKED_WITH_MARKET_HEALTH_WARNING}


def is_booked_status(status: str) -> bool:
    return status in BOOKED_STATUSES
