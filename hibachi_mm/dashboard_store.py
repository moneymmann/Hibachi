from __future__ import annotations

import time
from collections import deque
from typing import Any

from hibachi_mm.dashboard_events import DashboardEventBus
from hibachi_mm.state import StateStore


class DashboardStore:
    def __init__(self, state: StateStore, bus: DashboardEventBus):
        self.state = state
        self.bus = bus
        self.engine_status: dict[str, Any] = {"status": "HALTED", "mode": "inspect", "symbol": "", "uptime_sec": 0}
        self.account: dict[str, Any] = {}
        self.market: dict[str, Any] = {}
        self.risk: dict[str, Any] = {}
        self.position: dict[str, Any] = {}
        self.quote_decision: dict[str, Any] = {}
        self.started_at = int(time.time())
        self.price_curve: deque[dict[str, Any]] = deque(maxlen=3600)
        self.pnl_curve: deque[dict[str, Any]] = deque(maxlen=3600)
        self.spread_curve: deque[dict[str, Any]] = deque(maxlen=3600)

    async def publish_event(self, event_type: str, payload: dict[str, Any], level: str = "info") -> None:
        ts_ms = int(time.time() * 1000)
        body = {"ts_ms": ts_ms, "type": event_type, "level": level, "payload": payload}
        self.state.insert_event(ts_ms, level, event_type, str(payload))
        await self.bus.publish(body)

    async def update_engine_status(self, status: str, mode: str, symbol: str) -> None:
        now = int(time.time())
        self.engine_status = {
            "status": status,
            "mode": mode,
            "symbol": symbol,
            "uptime_sec": now - self.started_at,
            "last_heartbeat_ts": int(time.time() * 1000),
        }
        self.state.insert_heartbeat(self.engine_status["last_heartbeat_ts"], mode, status, symbol)
        await self.publish_event("engine_status", self.engine_status)

    async def update_market(self, rec: dict[str, Any]) -> None:
        self.market = rec
        self.state.insert_market_snapshot(rec)
        self.price_curve.append({"ts_ms": rec["ts_ms"], "mid": rec.get("mid"), "mark": rec.get("mark_price")})
        self.spread_curve.append({"ts_ms": rec["ts_ms"], "spread_bps": rec.get("spread_bps"), "net_edge_bps": rec.get("net_edge_bps")})
        await self.publish_event("market_snapshot", rec)

    async def update_account(self, rec: dict[str, Any]) -> None:
        self.account = rec
        self.position = {
            "qty": rec.get("position_qty", "0"),
            "notional": rec.get("position_notional", "0"),
            "direction": "LONG" if float(rec.get("position_qty", 0)) > 0 else "SHORT" if float(rec.get("position_qty", 0)) < 0 else "FLAT",
            "liquidation_risk_pct": rec.get("liquidation_risk_pct", "0"),
            "unrealized_pnl": rec.get("unrealized_pnl", "0"),
        }
        self.state.insert_account_snapshot(rec)
        self.state.insert_pnl_snapshot({
            "ts_ms": rec["ts_ms"],
            "equity": rec.get("equity", "0"),
            "realized_pnl": rec.get("realized_pnl", "0"),
            "unrealized_pnl": rec.get("unrealized_pnl", "0"),
            "total_pnl": str(float(rec.get("realized_pnl", 0)) + float(rec.get("unrealized_pnl", 0))),
        })
        self.pnl_curve.append({"ts_ms": rec["ts_ms"], "realized": rec.get("realized_pnl"), "unrealized": rec.get("unrealized_pnl"), "equity": rec.get("equity")})
        await self.publish_event("account_snapshot", rec)

    async def update_risk(self, rec: dict[str, Any]) -> None:
        self.risk = rec
        self.state.insert_risk_snapshot(rec)
        await self.publish_event("risk_snapshot", rec, level="warn" if rec.get("scenario") != "NORMAL_QUOTING" else "info")

    async def update_quote_decision(self, rec: dict[str, Any]) -> None:
        self.quote_decision = rec
        self.state.insert_quote_decision(rec)
        await self.publish_event("quote_decision", rec)

    def summary(self) -> dict[str, Any]:
        return {
            "engine": self.engine_status,
            "account": self.account,
            "risk": self.risk,
            "market": self.market,
            "position": self.position,
            "decision": self.quote_decision,
        }
