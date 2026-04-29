def enforce_one_per_side(orders):
    sides = {"buy": [], "sell": []}
    for o in orders:
        sides[o.get("side", "").lower()].append(o)
    return {k: v[:1] for k, v in sides.items()}
