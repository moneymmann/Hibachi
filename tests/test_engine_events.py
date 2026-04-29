import asyncio
import json
from pathlib import Path

from hibachi_mm.dashboard_events import DashboardEventBus
from hibachi_mm.dashboard_store import DashboardStore
from hibachi_mm.engine import TradingEngine
from hibachi_mm.state import StateStore
from test_strategy import make_config


class StubGateway:
    def fetch_market(self, symbol):
        return {
            "ts_ms": 1,
            "symbol": symbol,
            "best_bid": "10000",
            "best_ask": "10020",
            "mid": "10010",
            "mark_price": "10010",
            "predicted_funding": "0",
            "spread_bps": "19.98",
        }

    def fetch_account(self):
        return {
            "ts_ms": 1,
            "equity": "1000",
            "balance": "1000",
            "unrealized_pnl": "0",
            "realized_pnl": "0",
            "fee": "0",
            "funding_pnl": "0",
            "free_margin": "800",
            "free_margin_pct": "80",
            "total_order_notional": "0",
            "total_position_notional": "0",
            "leverage": "0",
            "position_qty": "0",
            "position_notional": "0",
            "liquidation_risk_pct": "0",
        }

    def place_limit_entry(self, *args, **kwargs):
        raise AssertionError("dry-run should not place orders")


def test_dry_run_audit_has_market_account_quote(tmp_path):
    cfg = make_config()
    cfg.state.sqlite_path = str(tmp_path / "db.sqlite")
    cfg.logging.audit_log_path = str(tmp_path / "audit.jsonl")
    state = StateStore(cfg.state.sqlite_path)
    store = DashboardStore(state, DashboardEventBus())
    engine = TradingEngine(cfg, mode="dry-run", store=store)
    engine.gateway = StubGateway()

    async def run_short():
        task = asyncio.create_task(engine.run())
        await asyncio.sleep(1.3)
        engine.stop()
        await task

    asyncio.run(run_short())
    txt = Path(cfg.logging.audit_log_path).read_text(encoding="utf-8")
    assert '"event": "market_snapshot"' in txt
    assert '"event": "account_snapshot"' in txt
    assert '"event": "quote_decision"' in txt
