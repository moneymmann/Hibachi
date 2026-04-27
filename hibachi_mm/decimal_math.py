from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

BPS = Decimal("10000")
HUNDRED = Decimal("100")
ZERO = Decimal("0")
ONE = Decimal("1")


def d(value: str | int | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def clamp(value: Decimal, minimum: Decimal, maximum: Decimal) -> Decimal:
    return min(max(value, minimum), maximum)


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= ZERO:
        raise ValueError("step must be > 0")
    units = (value / step).to_integral_value(rounding=ROUND_DOWN)
    return units * step


def bps(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator) * BPS
