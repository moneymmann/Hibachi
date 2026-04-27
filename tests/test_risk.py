from decimal import Decimal

from hibachi_mm.config import RiskConfig
from hibachi_mm.models import AccountState
from hibachi_mm.risk import evaluate_risk


def mk_account():
    return AccountState(
        equity_usdt=Decimal("1000"),
        account_balance=Decimal("1000"),
        total_unrealized_pnl=Decimal("0"),
        total_order_notional=Decimal("100"),
        total_position_notional=Decimal("200"),
        maker_fee_rate=Decimal("0"),
        taker_fee_rate=Decimal("0"),
        positions=[],
        current_symbol_position_qty=Decimal("0"),
        current_symbol_position_notional_signed=Decimal("0"),
    )


def test_stale_data_blocks_new_orders():
    status = evaluate_risk(RiskConfig(max_stale_market_data_ms=100), mk_account(), Decimal("0.05"), market_age_ms=101)
    assert not status.allow_new_orders


def test_free_margin_too_low_blocks():
    acc = mk_account()
    acc.total_position_notional = Decimal("19000")
    status = evaluate_risk(RiskConfig(min_free_margin_pct=Decimal("20")), acc, Decimal("0.05"), market_age_ms=1)
    assert not status.allow_new_orders
