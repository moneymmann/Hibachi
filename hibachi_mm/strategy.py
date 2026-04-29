from __future__ import annotations

from decimal import Decimal

from hibachi_mm.config import RiskConfig, StrategyConfig
from hibachi_mm.decimal_math import BPS, HUNDRED, ONE, ZERO, bps, clamp, floor_to_step
from hibachi_mm.models import AccountState, ContractRules, MarketSnapshot, QuoteDecision


def _top_notional(levels: list, n: int) -> Decimal:
    total = ZERO
    for lv in levels[:n]:
        total += lv.price * lv.qty
    return total


def make_quote_decision(
    strategy: StrategyConfig,
    risk: RiskConfig,
    market: MarketSnapshot,
    contract: ContractRules,
    account: AccountState,
    free_margin_approx: Decimal,
    free_margin_pct: Decimal,
) -> QuoteDecision:
    mid = (market.best_bid_price + market.best_ask_price) / Decimal("2")
    gross = bps((market.best_ask_price - market.best_bid_price), mid)

    candidate_bid = market.best_bid_price
    if strategy.use_inside_quote and market.best_bid_price + contract.tick_size < market.best_ask_price:
        candidate_bid = market.best_bid_price + contract.tick_size

    candidate_ask = market.best_ask_price
    if strategy.use_inside_quote and market.best_ask_price - contract.tick_size > market.best_bid_price:
        candidate_ask = market.best_ask_price - contract.tick_size

    if candidate_bid >= market.best_ask_price:
        return _blocked(mid, gross, "bid_crosses_ask")
    if candidate_ask <= market.best_bid_price:
        return _blocked(mid, gross, "ask_crosses_bid")
    if candidate_bid >= candidate_ask:
        return _blocked(mid, gross, "crossed_quotes")

    maker_fee_bps = account.maker_fee_rate * BPS
    net_edge = bps(candidate_ask - candidate_bid, mid) - (
        Decimal("2") * maker_fee_bps
        + strategy.latency_buffer_bps
        + strategy.adverse_selection_buffer_bps
        + strategy.funding_buffer_bps
        + strategy.mark_deviation_buffer_bps
    )
    if net_edge < strategy.min_net_edge_bps:
        return _blocked(mid, gross, "edge_below_threshold", net_edge=net_edge)

    raw_mult = ONE + max(ZERO, net_edge - strategy.min_net_edge_bps) / strategy.edge_size_ramp_bps
    edge_mult = clamp(raw_mult, ONE, strategy.max_edge_size_multiplier)

    if account.equity_usdt <= ZERO:
        return _blocked(mid, gross, "non_positive_equity", net_edge=net_edge)

    target_notional = account.equity_usdt * strategy.target_position_notional_pct / HUNDRED
    deviation = (account.current_symbol_position_notional_signed - target_notional) / account.equity_usdt
    bid_pos_mult = clamp(
        ONE - deviation * strategy.position_skew_strength,
        strategy.min_side_size_multiplier,
        strategy.max_side_size_multiplier,
    )
    ask_pos_mult = clamp(
        ONE + deviation * strategy.position_skew_strength,
        strategy.min_side_size_multiplier,
        strategy.max_side_size_multiplier,
    )

    if free_margin_pct < risk.min_free_margin_pct:
        return _blocked(mid, gross, "free_margin_too_low", net_edge=net_edge)

    base_margin = account.equity_usdt * strategy.entry_margin_pct / HUNDRED
    margin_cap = min(account.equity_usdt * strategy.max_order_margin_pct / HUNDRED, free_margin_approx * Decimal("0.50"))
    bid_margin = min(base_margin * edge_mult * bid_pos_mult, margin_cap)
    ask_margin = min(base_margin * edge_mult * ask_pos_mult, margin_cap)

    bid_notional = bid_margin / contract.initial_margin_rate
    ask_notional = ask_margin / contract.initial_margin_rate

    top_bid = _top_notional(market.orderbook_bids, strategy.top_depth_levels_for_cap)
    top_ask = _top_notional(market.orderbook_asks, strategy.top_depth_levels_for_cap)
    liq_cap = min(top_bid, top_ask) * strategy.top_liquidity_participation_pct / HUNDRED
    bid_notional = min(bid_notional, strategy.max_order_notional_usdt, liq_cap)
    ask_notional = min(ask_notional, strategy.max_order_notional_usdt, liq_cap)

    bid_qty = floor_to_step(bid_notional / candidate_bid, contract.step_size)
    ask_qty = floor_to_step(ask_notional / candidate_ask, contract.step_size)

    should_bid = bid_qty >= contract.min_order_size and (candidate_bid * bid_qty) >= contract.min_notional
    should_ask = ask_qty >= contract.min_order_size and (candidate_ask * ask_qty) >= contract.min_notional

    projected_long = abs(account.total_position_notional) + abs(account.total_order_notional) + (candidate_bid * bid_qty)
    projected_short = abs(account.total_position_notional) + abs(account.total_order_notional) + (candidate_ask * ask_qty)
    lev_bid = projected_long / account.equity_usdt
    lev_ask = projected_short / account.equity_usdt
    max_pos_notional = account.equity_usdt * risk.max_net_position_notional_pct / HUNDRED

    if lev_bid > strategy.max_total_leverage or abs(account.current_symbol_position_notional_signed + candidate_bid * bid_qty) > max_pos_notional:
        should_bid = False
    if lev_ask > strategy.max_total_leverage or abs(account.current_symbol_position_notional_signed - candidate_ask * ask_qty) > max_pos_notional:
        should_ask = False

    reason = "ok" if (should_bid or should_ask) else "filters_blocked_all"
    return QuoteDecision(
        should_bid=should_bid,
        should_ask=should_ask,
        bid_price=candidate_bid,
        bid_qty=bid_qty,
        ask_price=candidate_ask,
        ask_qty=ask_qty,
        mid=mid,
        gross_spread_bps=gross,
        net_edge_bps=net_edge,
        edge_size_multiplier=edge_mult,
        bid_position_multiplier=bid_pos_mult,
        ask_position_multiplier=ask_pos_mult,
        bid_margin_budget_usdt=bid_margin,
        ask_margin_budget_usdt=ask_margin,
        bid_notional_usdt=bid_notional,
        ask_notional_usdt=ask_notional,
        projected_long_notional=projected_long,
        projected_short_notional=projected_short,
        reason=reason,
    )


def _blocked(mid: Decimal, gross: Decimal, reason: str, net_edge: Decimal = ZERO) -> QuoteDecision:
    return QuoteDecision(
        should_bid=False,
        should_ask=False,
        bid_price=None,
        bid_qty=None,
        ask_price=None,
        ask_qty=None,
        mid=mid,
        gross_spread_bps=gross,
        net_edge_bps=net_edge,
        edge_size_multiplier=ONE,
        bid_position_multiplier=ONE,
        ask_position_multiplier=ONE,
        bid_margin_budget_usdt=ZERO,
        ask_margin_budget_usdt=ZERO,
        bid_notional_usdt=ZERO,
        ask_notional_usdt=ZERO,
        projected_long_notional=ZERO,
        projected_short_notional=ZERO,
        reason=reason,
    )
