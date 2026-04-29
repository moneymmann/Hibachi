class ExchangeAdapter:
    def __init__(self, client):
        self.client = client

    def parse_orderbook(self, ob):
        bid0 = ob.bid[0] if getattr(ob, 'bid', None) else None
        ask0 = ob.ask[0] if getattr(ob, 'ask', None) else None
        bp = float(getattr(bid0, 'price', 0.0))
        ap = float(getattr(ask0, 'price', 0.0))
        bq = float(getattr(bid0, 'quantity', 0.0))
        aq = float(getattr(ask0, 'quantity', 0.0))
        return bp, ap, bq, aq

    def fetch_market(self, symbol='BTC/USDT-P'):
        ob = self.client.get_orderbook(symbol=symbol, depth=20, granularity='P0')
        bid, ask, bq, aq = self.parse_orderbook(ob)
        mid = (bid + ask) / 2 if bid and ask else 0.0
        return {'best_bid': bid, 'best_ask': ask, 'mid': mid, 'bid_qty': bq, 'ask_qty': aq}

    def fetch_account(self):
        bal = self.client.get_capital_balance()
        info = self.client.get_account_info()
        eq = float(getattr(bal, 'balance', bal.get('balance', 0))) if hasattr(bal, '__dict__') or isinstance(bal, dict) else 0.0
        fees = getattr(info, 'fee', None) if not isinstance(info, dict) else info.get('fee', {})
        total_order = getattr(info, 'totalOrderNotional', 0) if not isinstance(info, dict) else info.get('totalOrderNotional', 0)
        total_pos = getattr(info, 'totalPositionNotional', 0) if not isinstance(info, dict) else info.get('totalPositionNotional', 0)
        return {'equity': eq, 'total_order_notional': float(total_order or 0), 'total_position_notional': float(total_pos or 0), 'fees': fees or {}}
