from decimal import Decimal

from hibachi_mm.config import BotConfig
from hibachi_mm.models import AccountState, ContractRules, Level, MarketSnapshot, Scenario
from hibachi_mm.strategy import StrategyEngine


def make_config() -> BotConfig:
    return BotConfig.model_validate({
        "exchange": {"venue": "hibachi", "environment": "production", "symbol": "BTC/USDT-P", "api_endpoint": "", "data_api_endpoint": "", "api_endpoint_env": "", "data_api_endpoint_env": "", "api_key_env": "", "account_id_env": "", "private_key_env": "", "public_key_env": "", "dedicated_subaccount_confirmed": False, "allow_unknown_open_orders": False},
        "strategy": {"entry_margin_pct": "2", "max_order_margin_pct": "5", "max_total_leverage": "1.5", "max_order_notional_usdt": "1000", "min_net_edge_bps": "1.5", "edge_size_ramp_bps": "4", "max_edge_size_multiplier": "3.5", "top_depth_levels_for_cap": 3, "top_liquidity_participation_pct": "20", "target_position_notional_pct": "0", "position_skew_strength": "2", "min_side_size_multiplier": "0.1", "max_side_size_multiplier": "2.5", "latency_buffer_bps": "0.8", "adverse_selection_buffer_bps": "2", "funding_buffer_bps": "0.7", "mark_deviation_buffer_bps": "0.7", "volatility_buffer_min_bps": "0.5", "volatility_buffer_max_bps": "8", "quote_interval_ms": 400, "quote_ttl_ms": 2500, "min_reprice_ticks": 1, "creation_deadline_sec": 2, "use_inside_quote": True, "use_post_only": True, "cancel_on_edge_loss": True},
        "inventory": {"max_net_position_notional_pct": "40", "inventory_resolution_threshold_pct": "20", "maker_rebalance_grace_ms": 1200, "adverse_move_soft_bps": "4", "adverse_move_hard_bps": "8", "flat_position_threshold_pct": "3"},
        "exit_policy": {"maker_entry_only": True, "emergency_taker_exit": True, "passive_reduce_only_alo": True, "passive_exit_timeout_ms": 1200, "aggressive_reduce_only_limit": True, "aggressive_limit_slippage_bps": "2.5", "aggressive_exit_timeout_ms": 800, "emergency_reduce_only_ioc": True, "emergency_market_close": True, "emergency_trigger_adverse_bps": "10", "emergency_trigger_drawdown_pct": "1.2", "emergency_trigger_free_margin_pct": "12", "emergency_trigger_liquidation_risk_pct": "60", "max_emergency_exit_slippage_bps": "35"},
        "risk": {"max_daily_loss_usdt": "25", "max_equity_drawdown_pct": "4", "min_free_margin_pct": "18", "max_stale_market_data_ms": 1800, "max_ws_silence_ms": 4000, "max_order_ack_ms": 1000, "max_cancel_ack_ms": 1000, "max_1s_mid_move_bps": "8", "max_5s_mid_move_bps": "18", "max_spread_bps_for_normal_mode": "60", "min_depth_usdt_for_quote": "5000", "funding_blackout_before_sec": 180, "funding_blackout_after_sec": 30, "max_abs_predicted_funding_bps": "5", "cancel_bot_orders_on_shutdown": True, "cancel_bot_orders_on_stale_data": True, "cancel_bot_orders_on_edge_loss": True, "cancel_bot_orders_on_daily_loss": True},
        "state": {"sqlite_path": "./state/test.sqlite"},
        "logging": {"audit_log_path": "./logs/test.jsonl"},
    })


def make_market(spread=Decimal("20")):
    bid = Decimal("10000")
    ask = bid + spread
    mid = (bid + ask) / 2
    return MarketSnapshot("BTC/USDT-P", bid, Decimal("10"), ask, Decimal("10"), [Level(Decimal("10000"), Decimal("100"))] * 3, [Level(Decimal("10010"), Decimal("100"))] * 3, mid, mid, mid, mid, Decimal("0"), 0)


def make_account(pos=Decimal("0"), eq=Decimal("1000")):
    return AccountState(eq, eq, Decimal("0"), Decimal("0"), abs(pos) * Decimal("10000"), Decimal("0.0002"), Decimal("0.0005"), pos, pos * Decimal("10000"), Decimal("800"), Decimal("80"), Decimal("0.5"), Decimal("10"), [], [])


def rules():
    return ContractRules("BTC/USDT-P", Decimal("0.1"), Decimal("0.001"), Decimal("0.001"), Decimal("5"), Decimal("0.05"), Decimal("0.025"), "trading")


def test_base_notional_near_400():
    dec = StrategyEngine(make_config()).compute_quote(make_market(), make_account(), rules(), Decimal("0.2"), Decimal("0.4"))
    assert dec.bid_notional_usdt >= Decimal("390")


def test_edge_increases_size():
    eng = StrategyEngine(make_config())
    low = eng.compute_quote(make_market(Decimal("6")), make_account(), rules(), Decimal("0.2"), Decimal("0.4"))
    high = eng.compute_quote(make_market(Decimal("20")), make_account(), rules(), Decimal("0.2"), Decimal("0.4"))
    assert high.bid_notional_usdt >= low.bid_notional_usdt


def test_long_skew_reduces_bid_increases_ask():
    dec = StrategyEngine(make_config()).compute_quote(make_market(), make_account(Decimal("2")), rules(), Decimal("0.2"), Decimal("0.4"))
    assert dec.bid_position_multiplier < dec.ask_position_multiplier


def test_spread_gone_blocks_quote():
    m = make_market(Decimal("0.1"))
    d = StrategyEngine(make_config()).compute_quote(m, make_account(), rules(), Decimal("0.2"), Decimal("0.4"))
    assert d.mode == Scenario.EDGE_GONE.value


def test_funding_blackout_blocks_entry():
    d = StrategyEngine(make_config()).compute_quote(make_market(), make_account(), rules(), Decimal("0.1"), Decimal("0.2"), funding_blackout=True)
    assert d.mode == Scenario.FUNDING_BLACKOUT.value


def test_high_leverage_blocks_one_side_expansion():
    acc = make_account(Decimal("1"))
    acc.total_leverage_approx = Decimal("2")
    d = StrategyEngine(make_config()).compute_quote(make_market(), acc, rules(), Decimal("0.1"), Decimal("0.2"))
    assert d.should_bid is False


def test_max_order_notional_cap_applies():
    cfg = make_config()
    cfg.strategy.max_order_notional_usdt = Decimal("200")
    d = StrategyEngine(cfg).compute_quote(make_market(Decimal("50")), make_account(), rules(), Decimal("0.1"), Decimal("0.2"))
    assert d.bid_notional_usdt <= Decimal("200")


def test_max_order_margin_cap_applies():
    cfg = make_config()
    cfg.strategy.max_order_margin_pct = Decimal("1")
    d = StrategyEngine(cfg).compute_quote(make_market(Decimal("50")), make_account(), rules(), Decimal("0.1"), Decimal("0.2"))
    assert d.bid_notional_usdt <= Decimal("200")  # 1000 * 1% / 0.05


def test_short_skew_increases_bid_reduces_ask():
    dec = StrategyEngine(make_config()).compute_quote(make_market(), make_account(Decimal("-2")), rules(), Decimal("0.2"), Decimal("0.4"))
    assert dec.bid_position_multiplier > dec.ask_position_multiplier


def test_mark_divergence_blocks_quote():
    m = make_market()
    m.mark_price = Decimal("50")
    d = StrategyEngine(make_config()).compute_quote(m, make_account(), rules(), Decimal("0.1"), Decimal("0.2"))
    assert d.mode == Scenario.MARK_INDEX_DIVERGENCE.value
