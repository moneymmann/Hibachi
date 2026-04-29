def allow_entry(free_margin_pct: float, min_free_margin_pct: float, stale: bool = False, unknown_orders: bool = False):
    if stale:
        return False, "stale_market_data"
    if unknown_orders:
        return False, "unknown_open_orders"
    if free_margin_pct < min_free_margin_pct:
        return False, "low_free_margin"
    return True, "ok"
