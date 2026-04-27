from decimal import Decimal

from hibachi_mm.models import Scenario
from hibachi_mm.scenario_manager import PositionEvent, ScenarioManager
from test_strategy import make_config


def test_post_only_reject_cooldown():
    sm = ScenarioManager(make_config())
    sm.on_post_only_reject("BUY", 1000)
    sm.on_post_only_reject("BUY", 1001)
    sm.on_post_only_reject("BUY", 1002)
    assert sm.can_quote_side("BUY", 2000) is False


def test_soft_to_aggressive_transition():
    sm = ScenarioManager(make_config())
    s = sm.inventory_scenario(PositionEvent(position_qty=Decimal("1"), adverse_move_bps=Decimal("4"), elapsed_ms_since_fill=100))
    assert s == Scenario.ONE_SIDE_FILLED_ADVERSE_SOFT
