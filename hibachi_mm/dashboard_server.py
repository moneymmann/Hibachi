from __future__ import annotations

import json
from pathlib import Path

from hibachi_mm.dashboard_store import DashboardStore
from hibachi_mm.state import StateStore


def create_dashboard_app(store: DashboardStore, state: StateStore):
    try:
        from fastapi import FastAPI, WebSocket
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles
    except Exception as exc:
        raise RuntimeError("FastAPI is required for dashboard") from exc

    app = FastAPI(title="Hibachi Spread Capture Control Center")
    static_dir = Path(__file__).resolve().parent / "dashboard_static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/dashboard")
    def dashboard() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/api/summary")
    def summary() -> dict:
        return store.summary()

    @app.get("/api/account")
    def account() -> dict:
        return store.account

    @app.get("/api/market")
    def market() -> dict:
        return store.market

    @app.get("/api/risk")
    def risk() -> dict:
        return store.risk

    @app.get("/api/position")
    def position() -> dict:
        return store.position

    @app.get("/api/open-orders")
    def open_orders() -> list[dict]:
        return state.list_open_orders()

    @app.get("/api/fills")
    def fills() -> list[dict]:
        return [dict(r) for r in state.query("SELECT * FROM fills ORDER BY ts_ms DESC LIMIT 200")]

    @app.get("/api/events")
    def events(limit: int = 200) -> list[dict]:
        rows = state.query("SELECT ts_ms, level, event_type, payload FROM events ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]

    @app.get("/api/equity-curve")
    def equity_curve() -> list[dict]:
        return [dict(r) for r in state.query("SELECT ts_ms, equity FROM pnl_snapshots ORDER BY ts_ms DESC LIMIT 500")]

    @app.get("/api/pnl-curve")
    def pnl_curve() -> list[dict]:
        return [dict(r) for r in state.query("SELECT ts_ms, realized_pnl, unrealized_pnl, total_pnl FROM pnl_snapshots ORDER BY ts_ms DESC LIMIT 500")]

    @app.get("/api/price-curve")
    def price_curve() -> list[dict]:
        return [dict(r) for r in state.query("SELECT ts_ms, mid, mark_price FROM market_snapshots ORDER BY ts_ms DESC LIMIT 500")]

    @app.get("/api/spread-curve")
    def spread_curve() -> list[dict]:
        return [dict(r) for r in state.query("SELECT ts_ms, spread_bps FROM market_snapshots ORDER BY ts_ms DESC LIMIT 500")]

    @app.get("/api/engine-status")
    def engine_status() -> dict:
        return store.engine_status

    @app.websocket("/ws/dashboard")
    async def ws_dashboard(ws: WebSocket) -> None:
        await ws.accept()
        q = await store.bus.subscribe()
        try:
            for item in store.bus.recent(100):
                await ws.send_text(json.dumps(item))
            while True:
                item = await q.get()
                await ws.send_text(json.dumps(item))
        finally:
            await store.bus.unsubscribe(q)

    return app
