from __future__ import annotations

import argparse

from hibachi_mm.config import load_config
from hibachi_mm.engine import LiveGateError, validate_live_gate
from hibachi_mm.security import run_security_checks


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("hibachi_mm")
    p.add_argument("command", choices=["inspect", "dry-run", "live", "security-check"])
    p.add_argument("--config", required=True)
    return p


def main() -> int:
    args = build_parser().parse_args()
    cfg = load_config(args.config)

    if args.command == "inspect":
        print(f"inspect ok: symbol={cfg.exchange.symbol}, env={cfg.exchange.environment}")
        return 0

    if args.command == "dry-run":
        report = run_security_checks(cfg, mode="dry-run")
        for w in report.warnings:
            print(f"[WARN] {w}")
        print("dry-run mode: no live orders are sent")
        return 0

    if args.command == "security-check":
        report = run_security_checks(cfg, mode="dry-run")
        for w in report.warnings:
            print(f"[WARN] {w}")
        for e in report.errors:
            print(f"[ERROR] {e}")
        print("security check passed" if report.ok else "security check failed")
        return 0 if report.ok else 3

    if args.command == "live":
        report = run_security_checks(cfg, mode="live")
        for w in report.warnings:
            print(f"[WARN] {w}")
        if not report.ok:
            for e in report.errors:
                print(f"[ERROR] {e}")
            return 3
        try:
            validate_live_gate(cfg, unknown_open_orders_count=0)
        except LiveGateError as exc:
            print(f"live gate blocked: {exc}")
            return 2
        print("live gate passed")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
