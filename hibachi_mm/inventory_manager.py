def skew_sizes(base_size: float, position_notional_pct: float, strength: float = 2.0):
    k = min(abs(position_notional_pct) / 100 * strength, 0.9)
    if position_notional_pct > 0:
        return base_size * (1 - k), base_size * (1 + k)
    if position_notional_pct < 0:
        return base_size * (1 + k), base_size * (1 - k)
    return base_size, base_size
