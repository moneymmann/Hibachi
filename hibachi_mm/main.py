from __future__ import annotations
import argparse
import asyncio
import os
import signal
import uvicorn
import yaml

from .audit import AuditLogger
from .dashboard import create_dashboard_app
from .engine import TradingEngine
from .exchange import HibachiExchange
from .state import init_db


def load_config(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def live_gate():
    if os.getenv("HIBACHI_ENABLE_LIVE_TRADING") != "I_UNDERSTAND_PERP_RISK":
        raise RuntimeError("live gate blocked")


async def run_engine(cfg: dict, mode: str):
    audit = AuditLogger(cfg["logging"]["audit_log_path"])
    init_db(cfg["state"]["sqlite_path"])
    ex = HibachiExchange(cfg, os.environ)
    eng = TradingEngine(cfg, ex, audit, mode=mode)
    loop = asyncio.get_running_loop()

    def stop(*_):
        eng.running = False

    try:
        loop.add_signal_handler(signal.SIGINT, stop)
    except (NotImplementedError, RuntimeError):
        signal.signal(signal.SIGINT, stop)
    await eng.run()


async def run_ui(cfg: dict, mode: str):
    audit_path = cfg["logging"]["audit_log_path"]
    app = create_dashboard_app(audit_path)
    server = uvicorn.Server(uvicorn.Config(app, host=cfg['exchange']['dashboard_host'], port=cfg['exchange']['dashboard_port'], log_level='warning'))
    await asyncio.gather(run_engine(cfg, mode), server.serve())


async def run_inspect(cfg: dict):
    ex = HibachiExchange(cfg, os.environ)
    m = await ex.get_market_snapshot()
    a = await ex.get_account_snapshot()
    print("best_bid", m.best_bid)
    print("best_ask", m.best_ask)
    print("mid", m.mid)
    print("equity", a.equity)
    print("free_margin", a.free_margin)
    print("current_position_qty", a.current_position_qty)
    print("maker_fee_rate", a.maker_fee_rate)
    print("taker_fee_rate", a.taker_fee_rate)


async def run_live_smoke(cfg: dict):
    live_gate()
    audit = AuditLogger(cfg["logging"]["audit_log_path"])
    ex = HibachiExchange(cfg, os.environ)
    m = await ex.get_market_snapshot()
    await ex.get_account_snapshot()
    px = m.best_bid
    audit.log("place_order_intent", mode="live", dry_run=False, side="buy", price=str(px))
    try:
        res = await ex.place_limit("buy", px, __import__('decimal').Decimal('0.001'))
        audit.log("order_submitted", mode="live", dry_run=False, response=str(res))
        oid = getattr(res, "order_id", None) if not isinstance(res, dict) else res.get("order_id")
        if oid:
            await asyncio.sleep(2)
            try:
                await ex.cancel_order(oid)
                audit.log("order_cancelled", order_id=str(oid))
            except Exception as ce:
                audit.log("cancel_error", error=str(ce))
    except Exception as e:
        audit.log("order_error", mode="live", dry_run=False, error=str(e))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd")
    p.add_argument("--config", required=True)
    a = p.parse_args()
    cfg = load_config(a.config)

    if a.cmd == "inspect":
        asyncio.run(run_inspect(cfg))
    elif a.cmd == "dry-run":
        asyncio.run(run_engine(cfg, "dry-run"))
    elif a.cmd == "dashboard":
        uvicorn.run(create_dashboard_app(cfg["logging"]["audit_log_path"]), host=cfg['exchange']['dashboard_host'], port=cfg['exchange']['dashboard_port'])
    elif a.cmd == "dry-run-ui":
        asyncio.run(run_ui(cfg, "dry-run"))
    elif a.cmd == "live-smoke":
        asyncio.run(run_live_smoke(cfg))
    elif a.cmd == "live-ui":
        live_gate()
        asyncio.run(run_ui(cfg, "live"))


if __name__ == "__main__":
    main()
