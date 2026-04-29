import time
from decimal import Decimal
from hibachi_mm.decimal_math import bps, HUNDRED, ZERO
from hibachi_mm.models import MarketSnapshot, AccountSnapshot, Level

class HibachiExchange:
    def __init__(self,cfg,api_client=None):
        try:
            from hibachi_xyz.env_setup import setup_environment
            setup_environment()
        except Exception:
            pass
        if api_client is None:
            from hibachi_xyz import HibachiApiClient
            api_client=HibachiApiClient()
        self.api=api_client; self.cfg=cfg
    def get_market_snapshot(self,symbol:str,tick_size:Decimal=Decimal('0.1'))->MarketSnapshot:
        ob=self.api.get_orderbook(symbol=symbol,depth=20,granularity=str(tick_size))
        bid=Decimal(str(ob['bestBidPrice'])); ask=Decimal(str(ob['bestAskPrice']))
        mid=(bid+ask)/Decimal('2')
        return MarketSnapshot(symbol,bid,ask,Decimal(str(ob['bestBidQty'])),Decimal(str(ob['bestAskQty'])),[Level(Decimal(str(p)),Decimal(str(q))) for p,q in ob.get('bids',[])],[Level(Decimal(str(p)),Decimal(str(q))) for p,q in ob.get('asks',[])],mid,bps(ask-bid,mid),int(time.time()*1000))
    def get_account_snapshot(self,symbol:str,initial_margin_rate:Decimal=Decimal('0.05'))->AccountSnapshot:
        cap=self.api.get_capital_balance(); info=self.api.get_account_info()
        eq=Decimal(str(cap.get('balance',0))); bal=Decimal(str(info.get('balance',0))); upnl=Decimal(str(info.get('totalUnrealizedPnl',0)))
        if eq<=ZERO: eq=bal+upnl
        toon=Decimal(str(info.get('totalOrderNotional',0))); tpon=Decimal(str(info.get('totalPositionNotional',0)))
        used=(abs(toon)+abs(tpon))*initial_margin_rate; free=max(ZERO,eq-used); fp=ZERO if eq<=ZERO else free/eq*HUNDRED
        qty=Decimal('0')
        for p in info.get('positions',[]):
            if p.get('symbol')==symbol: qty=Decimal(str(p.get('quantity',0)))
        return AccountSnapshot(eq,bal,upnl,toon,tpon,qty,Decimal(str(info.get('tradeMakerFeeRate',0))),Decimal(str(info.get('tradeTakerFeeRate',0))),free,fp)
    def get_pending_orders(self,symbol:str): return list(self.api.get_pending_orders(symbol=symbol))
    def place_entry_orders(self,symbol,bid_price,bid_qty,ask_price,ask_qty):
        rs=[]
        if bid_price and bid_qty: rs.append(self.api.place_limit_order(symbol=symbol,side='BID',price=str(bid_price),quantity=str(bid_qty),timeInForce='ALO',postOnly=True))
        if ask_price and ask_qty: rs.append(self.api.place_limit_order(symbol=symbol,side='ASK',price=str(ask_price),quantity=str(ask_qty),timeInForce='ALO',postOnly=True))
        return rs
    def place_exit_order(self,symbol,side,price,qty):
        return self.api.place_limit_order(symbol=symbol,side=side,price=str(price),quantity=str(qty),reduceOnly=True,timeInForce='ALO',postOnly=True)
