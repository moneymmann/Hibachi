from .models import QuoteDecision

def compute_expected_edge_bps(bid, ask, mid, maker_fee_bps, latency_bps, adverse_bps, funding_bps=0.0, mark_bps=0.0, exit_cost=0.0):
    gross = ((ask - bid) / mid) * 10000 if mid else 0.0
    return gross - 2 * maker_fee_bps - latency_bps - adverse_bps - funding_bps - mark_bps - exit_cost

def make_quote(best_bid, best_ask, tick_size, cfg, allow_entry=True):
    spread_ticks = int(round((best_ask - best_bid) / tick_size)) if tick_size else 0
    bid, ask = best_bid, best_ask
    if cfg.use_inside_quote and spread_ticks >= cfg.inside_quote_min_spread_ticks:
        bid = best_bid + tick_size
        ask = best_ask - tick_size
    if bid >= ask or bid >= best_ask or ask <= best_bid:
        return QuoteDecision(False, "crossed_prevented")
    mid = (best_bid + best_ask) / 2
    edge = compute_expected_edge_bps(bid, ask, mid, cfg.maker_fee_bps_override, cfg.latency_cost_bps, cfg.adverse_selection_min_bps)
    if spread_ticks < cfg.min_gross_spread_ticks:
        return QuoteDecision(False, "spread_too_narrow", bid, ask, edge)
    if not allow_entry:
        return QuoteDecision(False, "risk_blocked", bid, ask, edge)
    if edge < cfg.min_expected_edge_bps:
        return QuoteDecision(False, "edge_too_low", bid, ask, edge)
    return QuoteDecision(True, "ok", bid, ask, edge)
