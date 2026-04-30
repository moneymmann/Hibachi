import asyncio
from decimal import Decimal
from .strategy import decide_quote
from .risk import evaluate_risk
from .order_manager import OrderManager

class TradingEngine:
    def __init__(self,cfg,exchange,audit,store,dry_run=True):
        self.cfg=cfg; self.exchange=exchange; self.audit=audit; self.store=store; self.dry_run=dry_run; self.running=True; self.om=OrderManager(exchange,audit)
    def dec(self,v): return Decimal(str(v))
    async def run(self):
        self.audit.log('engine_started', mode='dry-run' if self.dry_run else 'live', dry_run=self.dry_run)
        while self.running:
            try:
                self.audit.log('heartbeat')
                market=await self.exchange.get_market_snapshot(); self.market=market; self.audit.log('market_snapshot', best_bid=str(market.best_bid), best_ask=str(market.best_ask), mid=str(market.mid))
                acct=await self.exchange.get_account_snapshot(); self.audit.log('account_snapshot', equity=str(acct.equity), free_margin=str(acct.free_margin), current_position_qty=str(acct.position_qty))
                pending=await self.exchange.get_pending_orders(); unknown=len(pending)
                risk=evaluate_risk(self.cfg, market, acct, unknown); self.audit.log('risk_snapshot', **risk)
                q=decide_quote(self.cfg,market,acct,risk['ok']); self.audit.log('quote_decision', should_quote=q.should_quote, reason=q.reason, expected_edge_bps=str(q.expected_edge_bps))
                self.store.snapshot.update({'mode':'dry-run' if self.dry_run else 'live','best_bid':str(market.best_bid),'best_ask':str(market.best_ask),'mid':str(market.mid),'equity':str(acct.equity),'free_margin':str(acct.free_margin),'reason':q.reason})
                if q.should_quote:
                    if self.dry_run: self.audit.log('order_intent', bid=str(q.bid_price), ask=str(q.ask_price), qty=str(q.size_qty))
                    else:
                        await self.om.place_entry('buy',q.bid_price,q.size_qty); await self.om.place_entry('sell',q.ask_price,q.size_qty)
                else: self.audit.log('no_order_reason', reason=q.reason)
            except Exception as e:
                self.audit.log('api_error', error=str(e))
            await asyncio.sleep(self.cfg['strategy']['quote_interval_ms']/1000)
