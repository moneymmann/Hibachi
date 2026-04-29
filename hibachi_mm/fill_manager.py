def take_profit_from_fill(side: str, fill_price: float, tick_size: float, ticks: int):
    if side.lower() == "buy":
        return {"side": "sell", "price": fill_price + tick_size * ticks, "reduce_only": True}
    return {"side": "buy", "price": fill_price - tick_size * ticks, "reduce_only": True}
