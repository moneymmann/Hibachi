from __future__ import annotations

from decimal import Decimal


def is_funding_blackout(seconds_to_funding: int, before: int, after: int) -> bool:
    return -after <= seconds_to_funding <= before


def funding_buffer(predicted_rate: Decimal | None, base_buffer_bps: Decimal) -> Decimal:
    if predicted_rate is None:
        return base_buffer_bps
    if abs(predicted_rate) > Decimal("0.0005"):
        return base_buffer_bps * Decimal("2")
    return base_buffer_bps
