from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, getcontext

getcontext().prec = 28
BPS = Decimal("10000")


def D(v: str | int | Decimal) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def clamp(v: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    return max(lo, min(hi, v))


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        raise ValueError("step must be positive")
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def bps_diff(a: Decimal, b: Decimal, base: Decimal) -> Decimal:
    if base == 0:
        return D("0")
    return ((a - b) / base) * BPS
