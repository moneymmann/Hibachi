from decimal import Decimal

from hibachi_mm.emergency_exit import EmergencyExitPolicy
from hibachi_mm.models import Scenario
from test_strategy import make_config


def test_hard_move_calls_emergency_ioc_or_market():
    out = EmergencyExitPolicy(make_config()).decide(Decimal("15"), Decimal("50"), Decimal("0"), Decimal("10"))
    assert out.scenario == Scenario.ONE_SIDE_FILLED_ADVERSE_HARD
    assert out.use_ioc or out.use_market


def test_emergency_cost_recorded_field_present():
    out = EmergencyExitPolicy(make_config()).decide(Decimal("15"), Decimal("5"), Decimal("2"), Decimal("70"))
    assert out.slippage_bps > Decimal("0")
