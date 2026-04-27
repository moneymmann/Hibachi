from decimal import Decimal

from hibachi_mm.config import RiskConfig, StrategyConfig
from hibachi_mm.models import AccountState, ContractRules, Level, MarketSnapshot
from hibachi_mm.strategy import make_quote_decision


def mk_account(position_notional=Decimal("0")):
    return AccountState(
        equity_usdt=Decimal("1000"),
        account_balance=Decimal("1000"),
        total_unrealized_pnl=Decimal("0"),
        total_order_notional=Decimal("0"),
        total_position_notional=abs(position_notional),
        maker_fee_rate=Decimal("0"),
        taker_fee_rate=Decimal("0.0005"),
        positions=[],
        current_symbol_position_qty=position_notional / Decimal("100"),
        current_symbol_position_notional_signed=position_notional,
    )


def mk_contract(min_notional=Decimal("10")):
    return ContractRules(
        symbol="BTC/USDT-P",
        tick_size=Decimal("1"),
        step_size=Decimal("0.001"),
        min_order_size=Decimal("0.001"),
        min_notional=min_notional,
        initial_margin_rate=Decimal("0.05"),
        maintenance_margin_rate=Decimal("0.025"),
        settlement_symbol="USDT",
        underlying_symbol="BTC",
        orderbook_granularities=["1"],
        status="TRADING",
    )


def mk_market():
    return MarketSnapshot(
        symbol="BTC/USDT-P",
        best_bid_price=Decimal("100"),
        best_bid_qty=Decimal("100"),
        best_ask_price=Decimal("104"),
        best_ask_qty=Decimal("100"),
        orderbook_bids=[Level(Decimal("100"), Decimal("100")), Level(Decimal("99"), Decimal("100"))],
        orderbook_asks=[Level(Decimal("104"), Decimal("100")), Level(Decimal("105"), Decimal("100"))],
        mark_price=None,
        spot_price=None,
        funding_rate_estimation=None,
        ts_ms=0,
    )


def test_base_notional_near_600():
    d = make_quote_decision(StrategyConfig(), RiskConfig(), mk_market(), mk_contract(), mk_account(), Decimal("1000"), Decimal("100"))
    assert d.bid_notional_usdt >= Decimal("590")


def test_edge_multiplier_increases_with_edge():
    cfg = StrategyConfig()
    low_mkt = mk_market()
    hi_mkt = mk_market()
    hi_mkt.best_ask_price = Decimal("110")
    low = make_quote_decision(cfg, RiskConfig(), low_mkt, mk_contract(), mk_account(), Decimal("1000"), Decimal("100"))
    high = make_quote_decision(cfg, RiskConfig(), hi_mkt, mk_contract(), mk_account(), Decimal("1000"), Decimal("100"))
    assert high.edge_size_multiplier >= low.edge_size_multiplier


def test_max_order_margin_cap():
    cfg = StrategyConfig(max_order_margin_pct=Decimal("1.0"))
    d = make_quote_decision(cfg, RiskConfig(), mk_market(), mk_contract(), mk_account(), Decimal("1000"), Decimal("100"))
    assert d.bid_notional_usdt <= Decimal("200")


def test_max_order_notional_cap():
    cfg = StrategyConfig(max_order_notional_usdt=Decimal("300"))
    d = make_quote_decision(cfg, RiskConfig(), mk_market(), mk_contract(), mk_account(), Decimal("1000"), Decimal("100"))
    assert d.bid_notional_usdt <= Decimal("300")


def test_position_skew_long_short():
    long_d = make_quote_decision(StrategyConfig(), RiskConfig(), mk_market(), mk_contract(), mk_account(Decimal("400")), Decimal("1000"), Decimal("100"))
    short_d = make_quote_decision(StrategyConfig(), RiskConfig(), mk_market(), mk_contract(), mk_account(Decimal("-400")), Decimal("1000"), Decimal("100"))
    assert long_d.ask_position_multiplier > long_d.bid_position_multiplier
    assert short_d.bid_position_multiplier > short_d.ask_position_multiplier


def test_min_notional_filter_blocks_orders():
    d = make_quote_decision(StrategyConfig(), RiskConfig(), mk_market(), mk_contract(min_notional=Decimal("99999")), mk_account(), Decimal("1000"), Decimal("100"))
    assert not d.should_bid and not d.should_ask


def test_crossing_candidate_blocks_bid_or_ask():
    m = mk_market()
    m.best_ask_price = Decimal("100")
    d = make_quote_decision(StrategyConfig(use_inside_quote=False), RiskConfig(), m, mk_contract(), mk_account(), Decimal("1000"), Decimal("100"))
    assert d.reason in {"bid_crosses_ask", "ask_crosses_bid", "crossed_quotes"}


def test_max_total_leverage_blocks_side():
    cfg = StrategyConfig(max_total_leverage=Decimal("0.2"))
    d = make_quote_decision(cfg, RiskConfig(), mk_market(), mk_contract(), mk_account(), Decimal("1000"), Decimal("100"))
    assert (not d.should_bid) or (not d.should_ask)
