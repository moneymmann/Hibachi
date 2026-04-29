from hibachi_mm.strategy import make_quote, compute_expected_edge_bps
from hibachi_mm.config import StrategyConfig

def test_spread_1tick_quote_decision():
    d=make_quote(100,101,1,StrategyConfig(min_expected_edge_bps=-10))
    assert d.allow_entry

def test_crossed_prevention():
    d=make_quote(100,101,1,StrategyConfig(use_inside_quote=True,inside_quote_min_spread_ticks=1))
    assert not d.allow_entry

def test_expected_edge():
    assert compute_expected_edge_bps(100,101,100.5,0,0,0)>0
