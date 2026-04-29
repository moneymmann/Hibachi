from __future__ import annotations

import argparse
import asyncio
import signal


from hibachi_mm.config import load_config
from hibachi_mm.dashboard_events import DashboardEventBus
from hibachi_mm.dashboard_store import DashboardStore
from hibachi_mm.engine import LiveGateError, TradingEngine, validate_live_gate
from hibachi_mm.security import run_security_checks
from hibachi_mm.state import StateStore


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("hibachi_mm")
    p.add_argument("command", choices=["inspect", "security-check", "dry-run", "live", "dashboard", "dry-run-ui", "live-ui"])
    p.add_argument("--config", required=True)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8787)
    return p


async def run_dashboard_only(store: DashboardStore, state: StateStore, host: str, port: int) -> None:
    import uvicorn
    from hibachi_mm.dashboard_server import create_dashboard_app

    app = create_dashboard_app(store, state)
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="info"))
    await server.serve()


async def run_engine_and_dashboard(cfg, mode: str, host: str, port: int) -> None:
    state = StateStore(cfg.state.sqlite_path)
    bus = DashboardEventBus()
    store = DashboardStore(state, bus)
    engine = TradingEngine(cfg, mode=mode, store=store)
    import uvicorn
    from hibachi_mm.dashboard_server import create_dashboard_app

    app = create_dashboard_app(store, state)
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="info"))

    engine_task = asyncio.create_task(engine.run())
    server_task = asyncio.create_task(server.serve())

    stop_event = asyncio.Event()

    def _stop(*_: object) -> None:
        engine.stop()
        server.should_exit = True
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            signal.signal(sig, lambda *_: _stop())

    await stop_event.wait()
    await asyncio.gather(engine_task, server_task, return_exceptions=True)


def main() -> int:
    args = build_parser().parse_args()
    cfg = load_config(args.config)

    if args.command == "inspect":
        print(f"inspect ok: symbol={cfg.exchange.symbol}, env={cfg.exchange.environment}")
        return 0

    if args.command == "security-check":
        report = run_security_checks(cfg, mode="dry-run")
        for w in report.warnings:
            print(f"[WARN] {w}")
        for e in report.errors:
            print(f"[ERROR] {e}")
        print("security check passed" if report.ok else "security check failed")
        return 0 if report.ok else 3

    if args.command == "dashboard":
        state = StateStore(cfg.state.sqlite_path)
        bus = DashboardEventBus()
        store = DashboardStore(state, bus)
        asyncio.run(run_dashboard_only(store, state, args.host, args.port))
        return 0

    if args.command == "dry-run":
        report = run_security_checks(cfg, mode="dry-run")
        for w in report.warnings:
            print(f"[WARN] {w}")
        state = StateStore(cfg.state.sqlite_path)
        store = DashboardStore(state, DashboardEventBus())
        engine = TradingEngine(cfg, mode="dry-run", store=store)
        try:
            asyncio.run(engine.run())
        except KeyboardInterrupt:
            engine.stop()
        return 0

    if args.command == "live":
        report = run_security_checks(cfg, mode="live")
        if not report.ok:
            for e in report.errors:
                print(f"[ERROR] {e}")
            return 3
        try:
            validate_live_gate(cfg, unknown_open_orders_count=0)
        except LiveGateError as exc:
            print(f"live gate blocked: {exc}")
            return 2
        state = StateStore(cfg.state.sqlite_path)
        store = DashboardStore(state, DashboardEventBus())
        engine = TradingEngine(cfg, mode="live", store=store)
        try:
            asyncio.run(engine.run())
        except KeyboardInterrupt:
            engine.stop()
        return 0

    if args.command in {"dry-run-ui", "live-ui"}:
        mode = "live" if args.command == "live-ui" else "dry-run"
        report = run_security_checks(cfg, mode=mode)
        if mode == "live":
            try:
                validate_live_gate(cfg, unknown_open_orders_count=0)
            except LiveGateError as exc:
                print(f"live gate blocked: {exc}")
                return 2
        if not report.ok:
            for e in report.errors:
                print(f"[ERROR] {e}")
            return 3
        try:
            asyncio.run(run_engine_and_dashboard(cfg, mode, args.host, args.port))
        except KeyboardInterrupt:
            pass
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
