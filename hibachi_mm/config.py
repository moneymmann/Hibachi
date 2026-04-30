from decimal import Decimal
from pathlib import Path
import yaml


def load_config(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def pick_env(name: str, env: str, envs: dict) -> str:
    return envs.get(f"{name}_{env.upper()}") or envs.get(name, "")


def d(v: str | int | float) -> Decimal:
    return Decimal(str(v))
