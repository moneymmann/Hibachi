from decimal import Decimal
from .models import QuoteDecision

def decide_quote(cfg, market, account, risk_ok=True):
    s=cfg['strategy']
    spread=market.best_ask-market.best_bid
    spread_ticks=int(spread/market.tick_size)
    if spread_ticks < int(s['min_gross_spread_ticks']): return QuoteDecision(False,'spread_too_small')
    bid=market.best_bid; ask=market.best_ask
    if s.get('use_inside_quote') and spread_ticks>=int(s['inside_quote_min_spread_ticks']):
        bid=market.best_bid+market.tick_size; ask=market.best_ask-market.tick_size
    if bid>=ask or bid>=market.best_ask or ask<=market.best_bid: return QuoteDecision(False,'crossed_quote')
    edge=((ask-bid)/market.mid)*Decimal('10000')-Decimal(str(s['latency_cost_bps']))-Decimal(str(s['adverse_selection_min_bps']))
    if edge < Decimal(str(s['min_expected_edge_bps'])): return QuoteDecision(False,'edge_too_low', expected_edge_bps=edge)
    qty=Decimal('0.001')
    if account.equity < Decimal('1'): return QuoteDecision(False,'below_min_order_size')
    return QuoteDecision(risk_ok,'risk_blocked' if not risk_ok else 'ok', bid, ask, edge, qty)
