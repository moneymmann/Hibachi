from decimal import Decimal
from hibachi_mm.exchange import HibachiExchange
class StubApi:
    def get_orderbook(self,**_): return {'bestBidPrice':'100','bestAskPrice':'101','bestBidQty':'2','bestAskQty':'2','bids':[['100','2']], 'asks':[['101','2']]}
    def get_capital_balance(self): return {'balance':'1000'}
    def get_account_info(self): return {'balance':'1000','totalUnrealizedPnl':'0','totalOrderNotional':'0','totalPositionNotional':'0','positions':[{'symbol':'BTC/USDT-P','quantity':'0'}],'tradeMakerFeeRate':'0','tradeTakerFeeRate':'0'}
    def get_pending_orders(self,**_): return []
def test_exchange_stub_market_snapshot(): ex=HibachiExchange(type('x',(),{'symbol':'BTC/USDT-P'})(),api_client=StubApi()); m=ex.get_market_snapshot('BTC/USDT-P',Decimal('0.1')); assert m.best_bid==Decimal('100')
def test_exchange_stub_account_snapshot(): ex=HibachiExchange(type('x',(),{'symbol':'BTC/USDT-P'})(),api_client=StubApi()); a=ex.get_account_snapshot('BTC/USDT-P'); assert a.equity==Decimal('1000')
