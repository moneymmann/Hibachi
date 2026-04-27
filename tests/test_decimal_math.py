from decimal import Decimal

from hibachi_mm.decimal_math import clamp, floor_to_step


def test_floor_to_step():
    assert floor_to_step(Decimal("1.234"), Decimal("0.01")) == Decimal("1.23")


def test_clamp():
    assert clamp(Decimal("10"), Decimal("1"), Decimal("5")) == Decimal("5")
