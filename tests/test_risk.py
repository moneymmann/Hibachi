from decimal import Decimal

from hibachi_mm.risk import RiskEngine
from hibachi_mm.models import Scenario
from tests.test_strategy import make_account, make_config, make_market


def test_stale_data_blocks_new_quote():
    eng = RiskEngine(make_config())
    out = eng.evaluate_market_health(make_market(), now_ms=5000, ws_silence_ms=0, move_1s_bps=Decimal("0"), move_5s_bps=Decimal("0"))
    assert out.scenario == Scenario.STALE_DATA


def test_volatility_shock_blocks_quote():
    eng = RiskEngine(make_config())
    out = eng.evaluate_market_health(make_market(), now_ms=100, ws_silence_ms=0, move_1s_bps=Decimal("10"), move_5s_bps=Decimal("0"))
    assert out.scenario == Scenario.VOLATILITY_SHOCK


def test_free_margin_shortage_halts():
    eng = RiskEngine(make_config())
    acc = make_account()
    acc.free_margin_pct = Decimal("5")
    out = eng.evaluate_account_limits(acc, daily_pnl=Decimal("0"), max_equity_seen=Decimal("1000"))
    assert out.scenario == Scenario.LIQUIDATION_RISK_HALT
