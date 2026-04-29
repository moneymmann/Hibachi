import argparse, os
from .config import load_config
from .engine import Engine


def require_live_gate():
    if os.getenv("HIBACHI_ENABLE_LIVE_TRADING") != "I_UNDERSTAND_PERP_RISK":
        raise SystemExit("live gate blocked")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["inspect", "security-check", "dry-run", "live", "dashboard", "dry-run-ui", "live-ui"])
    p.add_argument("--config", required=True)
    args = p.parse_args()
    cfg = load_config(args.config)
    if args.command in {"live", "live-ui"}:
        require_live_gate()
    e = Engine("live" if args.command.startswith("live") else "dry-run")
    if args.command == "inspect":
        print({"symbol": cfg.exchange.symbol, "market_snapshot": e.snapshot().__dict__, "account_snapshot": {"equity": 0}})
    elif args.command == "security-check":
        print("ok")
    else:
        print(f"{args.command} started")

if __name__ == "__main__":
    main()
