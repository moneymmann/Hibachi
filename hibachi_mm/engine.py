from __future__ import annotations
import asyncio
from decimal import Decimal


class TradingEngine:
    def __init__(self, cfg, exchange, audit, *, mode: str):
        self.cfg = cfg
        self.exchange = exchange
        self.audit = audit
        self.mode = mode
        self.dry_run = mode != "live"
        self.running = True

    async def run(self):
        self.audit.log("startup", mode=self.mode, dry_run=self.dry_run)
        while self.running:
            try:
                self.audit.log("heartbeat", mode=self.mode, dry_run=self.dry_run)
                market = await self.exchange.get_market_snapshot()
                self.audit.log("market_snapshot", best_bid=str(market.best_bid), best_ask=str(market.best_ask), mid=str(market.mid))
                account = await self.exchange.get_account_snapshot()
                self.audit.log(
                    "account_snapshot",
                    equity=str(account.equity),
                    free_margin=str(account.free_margin),
                    current_position_qty=str(account.current_position_qty),
                )
                risk_ok = account.free_margin > Decimal("0")
                self.audit.log("risk_snapshot", ok=risk_ok)
                spread_ticks = int((market.best_ask - market.best_bid) / market.tick_size)
                quote = spread_ticks >= 1
                self.audit.log("quote_decision", quote=quote, spread_ticks=spread_ticks)
                if quote:
                    if self.dry_run:
                        self.audit.log("order_intent", side="buy/sell", price="top-of-book")
                    else:
                        bid = market.best_bid
                        self.audit.log("place_order_intent", side="buy", price=str(bid), dry_run=False, mode="live")
                        try:
                            res = await self.exchange.place_limit("buy", bid, Decimal("0.001"), reduce_only=False)
                            self.audit.log("order_submitted", side="buy", response=str(res), dry_run=False, mode="live")
                        except Exception as e:
                            self.audit.log("order_error", error=str(e), dry_run=False, mode="live")
                else:
                    self.audit.log("no_order_reason", reason="spread_too_small")
            except Exception as e:
                self.audit.log("api_error", error=str(e), mode=self.mode)
            await asyncio.sleep(self.cfg["strategy"].get("quote_interval_ms", 1000) / 1000)
