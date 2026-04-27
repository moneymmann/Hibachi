from __future__ import annotations

from decimal import Decimal

from hibachi_mm.config import BotConfig
from hibachi_mm.decimal_math import BPS, D, clamp, floor_to_step
from hibachi_mm.models import AccountState, ContractRules, MarketSnapshot, QuoteDecision, Scenario


class StrategyEngine:
    def __init__(self, config: BotConfig):
        self.config = config

    def _top_depth_notional(self, levels: list, n: int) -> Decimal:
        return sum((lvl.price * lvl.qty for lvl in levels[:n]), D("0"))

    def compute_quote(self, market: MarketSnapshot, account: AccountState, rules: ContractRules, move_1s_bps: Decimal, move_5s_bps: Decimal, funding_blackout: bool = False) -> QuoteDecision:
        cfg = self.config.strategy
        risk_cfg = self.config.risk

        if rules.status.lower() not in {"trading", "normal"}:
            return self._no_quote(market, Scenario.MAINTENANCE_HALT.value, "contract not tradable")

        gross_spread_bps = ((market.best_ask_price - market.best_bid_price) / market.mid) * BPS
        if gross_spread_bps > risk_cfg.max_spread_bps_for_normal_mode:
            return self._no_quote(market, Scenario.LOW_DEPTH.value, "abnormal spread")

        if funding_blackout:
            return self._no_quote(market, Scenario.FUNDING_BLACKOUT.value, "funding blackout")

        if market.mark_price is not None:
            mark_div = abs((market.mid - market.mark_price) / market.mid) * BPS if market.mid > 0 else D("0")
            if mark_div > (risk_cfg.max_spread_bps_for_normal_mode / D("2")):
                return self._no_quote(market, Scenario.MARK_INDEX_DIVERGENCE.value, "mark/index divergence")

        candidate_bid = market.best_bid_price
        candidate_ask = market.best_ask_price
        if cfg.use_inside_quote:
            if market.best_bid_price + rules.tick_size < market.best_ask_price:
                candidate_bid = market.best_bid_price + rules.tick_size
            if market.best_ask_price - rules.tick_size > market.best_bid_price:
                candidate_ask = market.best_ask_price - rules.tick_size

        if candidate_bid >= market.best_ask_price or candidate_ask <= market.best_bid_price or candidate_bid >= candidate_ask:
            return self._no_quote(market, Scenario.EDGE_GONE.value, "invalid post-only price")

        maker_fee_bps = account.maker_fee_rate * BPS
        mark_deviation_bps = D("0")
        if market.mark_price is not None and market.mid > 0:
            mark_deviation_bps = abs((market.mid - market.mark_price) / market.mid) * BPS
        mark_buffer = max(cfg.mark_deviation_buffer_bps, mark_deviation_bps * D("0.5"))
        vol_bps = max(abs(move_1s_bps), abs(move_5s_bps) / D("2"))
        vol_buffer = clamp(vol_bps, cfg.volatility_buffer_min_bps, cfg.volatility_buffer_max_bps)

        funding_buffer = cfg.funding_buffer_bps
        net_edge_bps = ((candidate_ask - candidate_bid) / market.mid) * BPS - (D("2") * maker_fee_bps) - cfg.latency_buffer_bps - cfg.adverse_selection_buffer_bps - funding_buffer - mark_buffer - vol_buffer

        if net_edge_bps < cfg.min_net_edge_bps:
            return self._no_quote(market, Scenario.EDGE_GONE.value, "net edge below threshold", net_edge_bps, gross_spread_bps)

        raw_mult = D("1") + max(D("0"), net_edge_bps - cfg.min_net_edge_bps) / cfg.edge_size_ramp_bps
        edge_mult = clamp(raw_mult, D("1"), cfg.max_edge_size_multiplier)

        target_notional = account.equity_usdt * cfg.target_position_notional_pct / D("100")
        deviation = D("0") if account.equity_usdt == 0 else (account.current_position_notional_signed - target_notional) / account.equity_usdt
        bid_pos_mult = clamp(D("1") - deviation * cfg.position_skew_strength, cfg.min_side_size_multiplier, cfg.max_side_size_multiplier)
        ask_pos_mult = clamp(D("1") + deviation * cfg.position_skew_strength, cfg.min_side_size_multiplier, cfg.max_side_size_multiplier)

        base_margin = account.equity_usdt * cfg.entry_margin_pct / D("100")
        bid_margin_budget = min(base_margin * edge_mult * bid_pos_mult, min(account.equity_usdt * cfg.max_order_margin_pct / D("100"), account.free_margin_approx * D("0.40")))
        ask_margin_budget = min(base_margin * edge_mult * ask_pos_mult, min(account.equity_usdt * cfg.max_order_margin_pct / D("100"), account.free_margin_approx * D("0.40")))

        bid_notional_raw = bid_margin_budget / rules.initial_margin_rate
        ask_notional_raw = ask_margin_budget / rules.initial_margin_rate

        top_ask = self._top_depth_notional(market.orderbook_asks, cfg.top_depth_levels_for_cap)
        top_bid = self._top_depth_notional(market.orderbook_bids, cfg.top_depth_levels_for_cap)
        top_cap = min(top_ask, top_bid) * cfg.top_liquidity_participation_pct / D("100")
        if min(top_ask, top_bid) < risk_cfg.min_depth_usdt_for_quote:
            return self._no_quote(market, Scenario.LOW_DEPTH.value, "insufficient depth", net_edge_bps, gross_spread_bps)

        bid_notional = min(bid_notional_raw, cfg.max_order_notional_usdt, top_cap)
        ask_notional = min(ask_notional_raw, cfg.max_order_notional_usdt, top_cap)
        bid_qty = floor_to_step(bid_notional / candidate_bid, rules.step_size)
        ask_qty = floor_to_step(ask_notional / candidate_ask, rules.step_size)

        should_bid = bid_qty >= rules.min_order_size and (candidate_bid * bid_qty) >= rules.min_notional
        should_ask = ask_qty >= rules.min_order_size and (candidate_ask * ask_qty) >= rules.min_notional

        max_net_pos = self.config.inventory.max_net_position_notional_pct * account.equity_usdt / D("100")
        projected_bid_pos = abs(account.current_position_notional_signed + (candidate_bid * bid_qty))
        projected_ask_pos = abs(account.current_position_notional_signed - (candidate_ask * ask_qty))
        if projected_bid_pos > max_net_pos:
            should_bid = False
        if projected_ask_pos > max_net_pos:
            should_ask = False

        if account.free_margin_pct < self.config.risk.min_free_margin_pct or account.total_leverage_approx > cfg.max_total_leverage:
            if account.current_position_qty_signed > 0:
                should_bid = False
            elif account.current_position_qty_signed < 0:
                should_ask = False

        return QuoteDecision(
            mode=Scenario.NORMAL_QUOTING.value,
            should_bid=should_bid,
            should_ask=should_ask,
            bid_price=candidate_bid if should_bid else None,
            bid_qty=bid_qty if should_bid else None,
            ask_price=candidate_ask if should_ask else None,
            ask_qty=ask_qty if should_ask else None,
            mid=market.mid,
            gross_spread_bps=gross_spread_bps,
            net_edge_bps=net_edge_bps,
            edge_size_multiplier=edge_mult,
            bid_position_multiplier=bid_pos_mult,
            ask_position_multiplier=ask_pos_mult,
            bid_notional_usdt=bid_notional,
            ask_notional_usdt=ask_notional,
            reason="normal quoting",
        )

    def _no_quote(self, market: MarketSnapshot, scenario: str, reason: str, net_edge: Decimal = D("0"), gross: Decimal = D("0")) -> QuoteDecision:
        return QuoteDecision(
            mode=scenario,
            should_bid=False,
            should_ask=False,
            bid_price=None,
            bid_qty=None,
            ask_price=None,
            ask_qty=None,
            mid=market.mid,
            gross_spread_bps=gross,
            net_edge_bps=net_edge,
            edge_size_multiplier=D("1"),
            bid_position_multiplier=D("1"),
            ask_position_multiplier=D("1"),
            bid_notional_usdt=D("0"),
            ask_notional_usdt=D("0"),
            reason=reason,
        )
