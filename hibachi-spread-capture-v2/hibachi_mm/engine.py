import asyncio, time, json
from hibachi_mm.risk import evaluate
from hibachi_mm.strategy import decide

class TradingEngine:
    def __init__(self,mode,cfg,exchange,audit,db,store=None): self.mode=mode; self.cfg=cfg; self.exchange=exchange; self.audit=audit; self.db=db; self.store=store; self.running=True
    async def run(self,iterations:int|None=None):
        self.audit.log('startup',mode=self.mode)
        i=0
        while self.running:
            now=int(time.time()*1000); self.audit.log('heartbeat',mode=self.mode,ts_ms=now); self.db.put('engine_heartbeats',str(now))
            market=self.exchange.get_market_snapshot(self.cfg.exchange.symbol)
            self.audit.log('market_snapshot',best_bid=str(market.best_bid),best_ask=str(market.best_ask),mid=str(market.mid)); self.db.put('market_snapshots',json.dumps({'mid':str(market.mid)}))
            account=self.exchange.get_account_snapshot(self.cfg.exchange.symbol)
            self.audit.log('account_snapshot',equity=str(account.equity),free_margin_pct=str(account.free_margin_pct)); self.db.put('account_snapshots',json.dumps({'equity':str(account.equity)}))
            p=self.exchange.get_pending_orders(self.cfg.exchange.symbol)
            rr=evaluate(self.cfg.risk,0,account.free_margin_pct,abs(min(account.unrealized_pnl,0)),len(p),abs(account.total_position_notional),account.equity)
            self.audit.log('risk_snapshot',allow_entry=rr.allow_entry,reason=rr.reason); self.db.put('risk_snapshots',rr.reason)
            q=decide(self.cfg.strategy,market,account,initial_margin_rate=__import__("decimal").Decimal("0.05"))
            self.audit.log('quote_decision',reason=q.reason,net_edge_bps=str(q.net_edge_bps)); self.db.put('quote_decisions',q.reason)
            if self.store: await self.store.publish({'event':'tick','best_bid':str(market.best_bid),'best_ask':str(market.best_ask),'mid':str(market.mid),'equity':str(account.equity),'reason':q.reason})
            if rr.allow_entry and (q.should_bid or q.should_ask):
                self.audit.log('order_intent',mode=self.mode,bid_price=str(q.bid_price) if q.bid_price else None)
                if self.mode in {'live','live-ui'}:
                    try: self.exchange.place_entry_orders(self.cfg.exchange.symbol,q.bid_price if q.should_bid else None,q.bid_qty if q.should_bid else None,q.ask_price if q.should_ask else None,q.ask_qty if q.should_ask else None); self.audit.log('order_submitted')
                    except Exception as e: self.audit.log('order_error',error=str(e))
            else: self.audit.log('no_order_reason',reason=rr.reason if not rr.allow_entry else q.reason)
            i+=1
            if iterations is not None and i>=iterations: break
            await asyncio.sleep(self.cfg.strategy.quote_interval_ms/1000)
        self.audit.log('shutdown',mode=self.mode)
