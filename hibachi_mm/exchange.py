class ExchangeAdapter:
    def __init__(self, client):
        self.client = client

    def _price(self, level):
        if hasattr(level, 'price'):
            return float(level.price)
        if isinstance(level, dict):
            return float(level.get('price', 0))
        return 0.0

    def parse_orderbook(self, ob):
        bid = ob.bid[0] if hasattr(ob, 'bid') and ob.bid else {'price': 0}
        ask = ob.ask[0] if hasattr(ob, 'ask') and ob.ask else {'price': 0}
        return self._price(bid), self._price(ask)

    def normalize_pending_orders(self, payload):
        if isinstance(payload, list): return payload
        for key in ('orders','data','result','items'):
            v = getattr(payload,key,None) if not isinstance(payload, dict) else payload.get(key)
            if isinstance(v,list): return v
        return []

    def granularity(self, requested: str):
        return requested if requested in {'P0','P1'} else 'P0'
