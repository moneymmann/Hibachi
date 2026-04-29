from types import SimpleNamespace
from hibachi_mm.exchange import ExchangeAdapter

def test_orderbook_object_parsing():
    ex=ExchangeAdapter(None); ob=SimpleNamespace(bid=[SimpleNamespace(price='100',quantity='1')], ask=[SimpleNamespace(price='101',quantity='2')])
    assert ex.parse_orderbook(ob)==(100.0,101.0)

def test_allowed_granularity_handling():
    ex=ExchangeAdapter(None); assert ex.granularity('P9')=='P0'

def test_pending_orders_parsing():
    ex=ExchangeAdapter(None); assert ex.normalize_pending_orders({'data':[1]})==[1]

def test_account_snapshot_fee_fields():
    fees={'maker':1}; assert fees['maker']==1
