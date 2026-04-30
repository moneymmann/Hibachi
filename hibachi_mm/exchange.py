from decimal import Decimal
import anyio
from .models import MarketSnapshot, AccountSnapshot

ALLOWED_GRANULARITY={Decimal('0.1'),Decimal('1'),Decimal('10'),Decimal('100')}

def _get(obj,*names,default=None):
    for n in names:
        if isinstance(obj,dict) and n in obj: return obj[n]
        if hasattr(obj,n): return getattr(obj,n)
    return default

def _level_px_qty(level):
    return Decimal(str(_get(level,'price'))), Decimal(str(_get(level,'quantity','qty',default='0')))

class HibachiExchange:
    def __init__(self,cfg:dict,env:dict):
        from hibachi_xyz import HibachiApiClient
        ex=cfg['exchange']; e=ex['environment'].upper()
        self.client=HibachiApiClient(api_url=env.get(f'HIBACHI_API_ENDPOINT_{e}') or env.get('HIBACHI_API_ENDPOINT'),data_api_url=env.get(f'HIBACHI_DATA_API_ENDPOINT_{e}') or env.get('HIBACHI_DATA_API_ENDPOINT'),api_key=env.get(f'HIBACHI_API_KEY_{e}') or env.get('HIBACHI_API_KEY'),account_id=env.get(f'HIBACHI_ACCOUNT_ID_{e}') or env.get('HIBACHI_ACCOUNT_ID'),private_key=env.get(f'HIBACHI_PRIVATE_KEY_{e}') or env.get('HIBACHI_PRIVATE_KEY'))
        self.symbol=ex['symbol']; self.timeout=ex.get('api_timeout_sec',5)
    async def _call(self,fn,*a,**kw):
        return await anyio.fail_after(self.timeout, anyio.to_thread.run_sync, lambda: fn(*a,**kw))
    async def get_market_snapshot(self):
        ob=await anyio.to_thread.run_sync(lambda:self.client.get_orderbook(self.symbol))
        bids=_get(ob,'bids','bid',default=[]); asks=_get(ob,'asks','ask',default=[])
        bp,_=_level_px_qty(bids[0]); ap,_=_level_px_qty(asks[0]); mid=(bp+ap)/Decimal('2')
        tk=Decimal(str(_get(ob,'tick_size','price_increment',default='1')))
        if tk not in ALLOWED_GRANULARITY: tk=Decimal('1')
        return MarketSnapshot(bp,ap,mid,tk)
    async def get_account_snapshot(self):
        cap=await anyio.to_thread.run_sync(self.client.get_capital_balance)
        inf=await anyio.to_thread.run_sync(self.client.get_account_info)
        return AccountSnapshot(Decimal(str(_get(cap,'equity','total_equity',default='0'))),Decimal(str(_get(cap,'free_margin','available_margin',default='0'))),Decimal(str(_get(inf,'position_qty','net_position_qty',default='0'))),Decimal(str(_get(inf,'maker_fee_rate',default='0'))),Decimal(str(_get(inf,'taker_fee_rate',default='0'))))
    async def get_pending_orders(self):
        r=await anyio.to_thread.run_sync(lambda:self.client.get_pending_orders(self.symbol))
        for n in ('orders','data','result','items','pending_orders'):
            v=_get(r,n)
            if v is not None: return list(v)
        return list(r) if isinstance(r,list) else []
    async def place_entry_order(self, side, price, qty, post_only=True, reduce_only=False):
        return await anyio.to_thread.run_sync(lambda:self.client.place_order(symbol=self.symbol, side=side, price=float(price), quantity=float(qty), post_only=post_only, reduce_only=reduce_only))
    async def place_reduce_only_take_profit(self, side, price, qty):
        return await self.place_entry_order(side,price,qty,post_only=True,reduce_only=True)
    async def cancel_order(self, order_id): return await anyio.to_thread.run_sync(lambda:self.client.cancel_order(order_id=order_id))
    async def replace_order(self, order_id, price, qty): return await anyio.to_thread.run_sync(lambda:self.client.replace_order(order_id=order_id, price=float(price), quantity=float(qty)))
    async def get_fills(self): return await anyio.to_thread.run_sync(lambda:self.client.get_fills(symbol=self.symbol))
