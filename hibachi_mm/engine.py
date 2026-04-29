import time
from .strategy import make_quote
from .risk import allow_entry

class Engine:
    def __init__(self, exchange, cfg, audit, mode='dry-run'):
        self.exchange=exchange; self.cfg=cfg; self.audit=audit; self.mode=mode

    def step(self):
        m = self.exchange.fetch_market(self.cfg.exchange.symbol)
        a = self.exchange.fetch_account()
        ok, reason = allow_entry(100.0, self.cfg.risk.min_free_margin_pct, stale=False, unknown_orders=False)
        q = make_quote(m['best_bid'], m['best_ask'], 0.1, self.cfg.strategy, allow_entry=ok)
        self.audit.log('heartbeat', mode=self.mode)
        self.audit.log('market_snapshot', **m)
        self.audit.log('account_snapshot', **a)
        self.audit.log('risk_snapshot', allow_entry=ok, reason=reason)
        self.audit.log('quote_decision', allow_entry=q.allow_entry, reason=q.reason, bid=q.bid_price, ask=q.ask_price)
        if self.mode == 'dry-run':
            self.audit.log('order_intent', dry_run=True)
        return m,a,q

    def run_forever(self, interval_ms=1000):
        self.audit.log('startup', mode=self.mode)
        while True:
            self.step()
            time.sleep(interval_ms/1000)
