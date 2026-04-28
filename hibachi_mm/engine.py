from __future__ import annotations

import asyncio
import logging
import os
import time
from decimal import Decimal
from pathlib import Path

from hibachi_mm.audit import AuditLogger
from hibachi_mm.config import BotConfig
from hibachi_mm.dashboard_store import DashboardStore
from hibachi_mm.exchange import HibachiGateway
from hibachi_mm.models import AccountState, ContractRules, Level, MarketSnapshot
from hibachi_mm.risk import RiskEngine
from hibachi_mm.strategy import StrategyEngine

LIVE_ACK = "I_UNDERSTAND_PERP_RISK"


class LiveGateError(RuntimeError):
    pass


def validate_live_gate(config: BotConfig, unknown_open_orders_count: int) -> None:
    if os.getenv("HIBACHI_ENABLE_LIVE_TRADING") != LIVE_ACK:
        raise LiveGateError("HIBACHI_ENABLE_LIVE_TRADING is not acknowledged")
    if config.exit_policy.maker_entry_only and not config.exit_policy.emergency_taker_exit:
        raise LiveGateError("maker_only_exit mode is forbidden in live")
    if (not config.exchange.allow_unknown_open_orders) and unknown_open_orders_count > 0:
        raise LiveGateError("unknown open orders exist")


def can_enable_cancel_on_disconnect(config: BotConfig) -> bool:
    return bool(config.exchange.dedicated_subaccount_confirmed)


class TradingEngine:
    def __init__(self, config: BotConfig, mode: str, store: DashboardStore):
        self.config = config
        self.mode = mode
        self.store = store
        self.gateway = HibachiGateway(config)
        self.strategy = StrategyEngine(config)
        self.risk = RiskEngine(config)
        self.audit = AuditLogger(config.logging.audit_log_path)
        Path("logs").mkdir(parents=True, exist_ok=True)
        console_name = "live" if mode == "live" else "dryrun"
        self.console_logger = logging.getLogger(f"hibachi.{mode}")
        self.console_logger.setLevel(logging.INFO)
        if not self.console_logger.handlers:
            self.console_logger.addHandler(logging.FileHandler(f"logs/{console_name}-console.log", encoding="utf-8"))
        self._running = False

    async def run(self) -> None:
        self._running = True
        await self.store.update_engine_status("STARTING", self.mode, self.config.exchange.symbol)
        self.audit.log("startup", {"mode": self.mode, "symbol": self.config.exchange.symbol})
        while self._running:
            now_ms = int(time.time() * 1000)
            try:
                market = self.gateway.fetch_market(self.config.exchange.symbol)
                account = self.gateway.fetch_account()
                if market:
                    await self.store.update_market({**market, "net_edge_bps": self.store.quote_decision.get("net_edge_bps", "0")})
                if account:
                    await self.store.update_account(account)

                if market and account:
                    snapshot = MarketSnapshot(
                        symbol=self.config.exchange.symbol,
                        best_bid_price=Decimal(market["best_bid"]),
                        best_bid_qty=Decimal("1"),
                        best_ask_price=Decimal(market["best_ask"]),
                        best_ask_qty=Decimal("1"),
                        orderbook_bids=[Level(Decimal(market["best_bid"]), Decimal("10")) for _ in range(3)],
                        orderbook_asks=[Level(Decimal(market["best_ask"]), Decimal("10")) for _ in range(3)],
                        mid=Decimal(market["mid"]),
                        mark_price=Decimal(market["mark_price"]),
                        spot_price=None,
                        last_trade_price=None,
                        predicted_funding_rate=Decimal(market["predicted_funding"]),
                        ts_ms=now_ms,
                    )
                    acc = AccountState(
                        equity_usdt=Decimal(account["equity"]),
                        account_balance=Decimal(account["balance"]),
                        total_unrealized_pnl=Decimal(account["unrealized_pnl"]),
                        total_order_notional=Decimal(account["total_order_notional"]),
                        total_position_notional=Decimal(account["total_position_notional"]),
                        maker_fee_rate=Decimal("0.0002"),
                        taker_fee_rate=Decimal("0.0005"),
                        current_position_qty_signed=Decimal(account["position_qty"]),
                        current_position_notional_signed=Decimal(account["position_notional"]),
                        free_margin_approx=Decimal(account["free_margin"]),
                        free_margin_pct=Decimal(account["free_margin_pct"]),
                        total_leverage_approx=Decimal(account["leverage"]),
                        liquidation_risk_pct_approx=Decimal(account["liquidation_risk_pct"]),
                        pending_bot_orders=[],
                        pending_unknown_orders=[],
                    )
                    rules = ContractRules(self.config.exchange.symbol, Decimal("0.1"), Decimal("0.001"), Decimal("0.001"), Decimal("5"), Decimal("0.05"), Decimal("0.025"), "trading")
                    risk_result = self.risk.evaluate_market_health(snapshot, now_ms, 0, Decimal("0"), Decimal("0"))
                    await self.store.update_risk({"ts_ms": now_ms, "scenario": risk_result.scenario.value, "free_margin_pct": account["free_margin_pct"], "leverage": account["leverage"], "liquidation_risk_pct": account["liquidation_risk_pct"], "reason": risk_result.reason})
                    q = self.strategy.compute_quote(snapshot, acc, rules, Decimal("0"), Decimal("0"), funding_blackout=False)
                    qrec = {
                        "ts_ms": now_ms,
                        "scenario": q.mode,
                        "should_bid": q.should_bid,
                        "should_ask": q.should_ask,
                        "bid_price": str(q.bid_price) if q.bid_price else None,
                        "bid_qty": str(q.bid_qty) if q.bid_qty else None,
                        "ask_price": str(q.ask_price) if q.ask_price else None,
                        "ask_qty": str(q.ask_qty) if q.ask_qty else None,
                        "gross_spread_bps": str(q.gross_spread_bps),
                        "net_edge_bps": str(q.net_edge_bps),
                        "reason": q.reason,
                    }
                    await self.store.update_quote_decision(qrec)
                    if self.mode == "dry-run" and (q.should_bid or q.should_ask):
                        await self.store.publish_event("order_submitted", {"type": "place_order_intent", "decision": qrec})
                    if self.mode == "live" and q.should_bid and q.bid_price and q.bid_qty:
                        res = self.gateway.place_limit_entry(self.config.exchange.symbol, "BUY", q.bid_price, q.bid_qty, post_only=True)
                        await self.store.publish_event("order_submitted", {"side": "BUY", "response": str(res)})

                await self.store.update_engine_status("RUNNING", self.mode, self.config.exchange.symbol)
                self.audit.log("heartbeat", {"mode": self.mode, "status": "RUNNING"})
                await self.store.publish_event("heartbeat", {"status": "RUNNING", "mode": self.mode})
            except Exception as exc:
                await self.store.update_engine_status("ERROR", self.mode, self.config.exchange.symbol)
                await self.store.publish_event("error", {"message": str(exc)}, level="error")
                self.audit.log("error", {"message": str(exc)})
                self.console_logger.error(str(exc))
            await asyncio.sleep(1)

        await self.store.update_engine_status("SHUTTING_DOWN", self.mode, self.config.exchange.symbol)
        self.audit.log("shutdown", {"mode": self.mode})
        await self.store.publish_event("engine_status", {"status": "HALTED", "mode": self.mode})

    def stop(self) -> None:
        self._running = False
