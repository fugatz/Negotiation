from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "fixtures"


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def money(value: float) -> int:
    return int(round(value / 100.0) * 100)


def weighted_average(parts: list[tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in parts)
    if total_weight == 0:
        return 0.0
    return sum(value * weight for value, weight in parts) / total_weight
