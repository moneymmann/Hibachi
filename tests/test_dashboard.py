import asyncio
from pathlib import Path

import pytest

try:
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except Exception:
    FASTAPI_AVAILABLE = False

from hibachi_mm.dashboard_events import DashboardEventBus
from hibachi_mm.dashboard_store import DashboardStore
from hibachi_mm.engine import TradingEngine
from hibachi_mm.state import StateStore
from test_strategy import make_config

if FASTAPI_AVAILABLE:
    from hibachi_mm.dashboard_server import create_dashboard_app


def make_store(tmp_path):
    cfg = make_config()
    cfg.state.sqlite_path = str(tmp_path / "db.sqlite")
    cfg.logging.audit_log_path = str(tmp_path / "audit.jsonl")
    state = StateStore(cfg.state.sqlite_path)
    store = DashboardStore(state, DashboardEventBus())
    return cfg, state, store


def test_dashboard_dependency_or_placeholder():
    assert True


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi missing")
def test_dashboard_health_and_summary(tmp_path):
    cfg, state, store = make_store(tmp_path)
    app = create_dashboard_app(store, state)
    c = TestClient(app)
    assert c.get("/health").status_code == 200
    assert c.get("/api/summary").status_code == 200


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi missing")
def test_dashboard_static_page(tmp_path):
    cfg, state, store = make_store(tmp_path)
    app = create_dashboard_app(store, state)
    c = TestClient(app)
    r = c.get("/dashboard")
    assert r.status_code == 200
    assert "Hibachi Spread Capture Control Center" in r.text


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi missing")
def test_websocket_event_stream(tmp_path):
    cfg, state, store = make_store(tmp_path)
    app = create_dashboard_app(store, state)
    c = TestClient(app)

    async def emit():
        await store.publish_event("heartbeat", {"x": 1})

    asyncio.run(emit())
    with c.websocket_connect("/ws/dashboard") as ws:
        msg = ws.receive_text()
        assert "heartbeat" in msg


def test_engine_heartbeat_and_event_written(tmp_path):
    cfg, state, store = make_store(tmp_path)
    engine = TradingEngine(cfg, mode="dry-run", store=store)

    async def run_short():
        task = asyncio.create_task(engine.run())
        await asyncio.sleep(1.2)
        engine.stop()
        await asyncio.sleep(0.2)
        await task

    asyncio.run(run_short())
    events = state.query("SELECT * FROM events")
    heartbeats = state.query("SELECT * FROM engine_heartbeats")
    assert len(events) > 0
    assert len(heartbeats) > 0
    assert Path(cfg.logging.audit_log_path).exists()
    assert Path("logs").exists()
