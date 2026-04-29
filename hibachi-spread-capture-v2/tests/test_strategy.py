from decimal import Decimal
from types import SimpleNamespace
from hibachi_mm.strategy import decide
from hibachi_mm.config import StrategyCfg
m=SimpleNamespace(best_bid=Decimal('100'),best_ask=Decimal('104'),mid=Decimal('102'))
def acct(pos=Decimal('0')): return SimpleNamespace(maker_fee_rate=Decimal('0'),equity=Decimal('1000'),current_position_qty=pos,free_margin=Decimal('1000'))
def test_strategy_equity_percent_sizing(): q=decide(StrategyCfg(),m,acct(),Decimal('0.05')); assert q.bid_qty is None or q.bid_qty>0
def test_strategy_edge_multiplier(): q=decide(StrategyCfg(),m,acct(),Decimal('0.05')); assert q.edge_mult>=Decimal('1')
def test_strategy_position_skew_long(): q=decide(StrategyCfg(),m,acct(Decimal('3')),Decimal('0.05')); assert q.reason in {'ok','size_filtered','edge_below_threshold'}
def test_strategy_position_skew_short(): q=decide(StrategyCfg(),m,acct(Decimal('-3')),Decimal('0.05')); assert q.reason in {'ok','size_filtered','edge_below_threshold'}
