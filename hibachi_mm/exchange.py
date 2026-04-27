from __future__ import annotations

from decimal import Decimal


def decimal_to_sdk_float(v: Decimal) -> float:
    """Single adapter boundary: Decimal -> string -> float."""
    return float(str(v))
