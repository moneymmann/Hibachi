from __future__ import annotations

import argparse

from dotenv import load_dotenv

from hibachi_mm.config import load_config
from hibachi_mm.engine import run_mode


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Hibachi spread-capture MM bot")
    p.add_argument("mode", choices=["inspect", "dry-run", "live"])
    p.add_argument("--config", required=True)
    return p


def main() -> int:
    load_dotenv()
    args = build_parser().parse_args()
    cfg = load_config(args.config)
    return run_mode(args.mode, cfg)


if __name__ == "__main__":
    raise SystemExit(main())
