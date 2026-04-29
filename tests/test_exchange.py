from types import SimpleNamespace
from hibachi_mm.exchange import ExchangeAdapter

class StubClient:
    def get_orderbook(self, **_):
        return SimpleNamespace(bid=[SimpleNamespace(price='60000', quantity='1')], ask=[SimpleNamespace(price='60001', quantity='1')])

def test_orderbook_object_parsing():
    ex=ExchangeAdapter(StubClient())
    ob=StubClient().get_orderbook()
    bid,ask,bq,aq=ex.parse_orderbook(ob)
    assert bid==60000.0 and ask==60001.0 and bq==1.0 and aq==1.0
