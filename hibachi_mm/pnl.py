def drawdown_pct(start_equity: float, current_equity: float) -> float:
    if start_equity <= 0:
        return 0.0
    return max(0.0, (start_equity - current_equity) / start_equity * 100)
