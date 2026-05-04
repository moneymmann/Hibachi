from decimal import Decimal
from types import SimpleNamespace
from hibachi_mm.strategy import decide_quote

def test_strategy_quote():
    cfg={'strategy':{'min_gross_spread_ticks':1,'use_inside_quote':False,'inside_quote_min_spread_ticks':3,'latency_cost_bps':'0','adverse_selection_min_bps':'0','min_expected_edge_bps':'0'}}
    m=SimpleNamespace(best_bid=Decimal('100'),best_ask=Decimal('101'),mid=Decimal('100.5'),tick_size=Decimal('1'))
    a=SimpleNamespace(equity=Decimal('100'),free_margin=Decimal('80'))
    assert decide_quote(cfg,m,a,True).should_quote
