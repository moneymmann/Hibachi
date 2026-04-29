from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ExchangeConfig:
    venue: str = "hibachi"
    environment: str = "production"
    symbol: str = "BTC/USDT-P"
    api_endpoint_env: str = "HIBACHI_API_ENDPOINT_PRODUCTION"
    data_api_endpoint_env: str = "HIBACHI_DATA_API_ENDPOINT_PRODUCTION"
    api_key_env: str = "HIBACHI_API_KEY_PRODUCTION"
    account_id_env: str = "HIBACHI_ACCOUNT_ID_PRODUCTION"
    private_key_env: str = "HIBACHI_PRIVATE_KEY_PRODUCTION"
    public_key_env: str = "HIBACHI_PUBLIC_KEY_PRODUCTION"
    api_endpoint: str = "https://api.hibachi.xyz"
    data_api_endpoint: str = "https://data-api.hibachi.xyz"
    dedicated_subaccount_confirmed: bool = False
    allow_unknown_open_orders: bool = False


@dataclass(slots=True)
class StrategyConfig:
    sizing_mode: str = "equity_percent_margin"
    entry_margin_pct: Decimal = Decimal("3.0")
    max_order_margin_pct: Decimal = Decimal("8.0")
    max_total_leverage: Decimal = Decimal("2.0")
    max_order_notional_usdt: Decimal = Decimal("1500")
    min_net_edge_bps: Decimal = Decimal("1.2")
    edge_size_ramp_bps: Decimal = Decimal("4.0")
    max_edge_size_multiplier: Decimal = Decimal("4.0")
    top_depth_levels_for_cap: int = 3
    top_liquidity_participation_pct: Decimal = Decimal("25.0")
    target_position_notional_pct: Decimal = Decimal("0.0")
    position_skew_strength: Decimal = Decimal("1.8")
    min_side_size_multiplier: Decimal = Decimal("0.20")
    max_side_size_multiplier: Decimal = Decimal("2.00")
    latency_buffer_bps: Decimal = Decimal("0.6")
    adverse_selection_buffer_bps: Decimal = Decimal("1.5")
    funding_buffer_bps: Decimal = Decimal("0.5")
    mark_deviation_buffer_bps: Decimal = Decimal("0.5")
    quote_interval_ms: int = 500
    quote_ttl_ms: int = 3500
    min_reprice_ticks: int = 1
    creation_deadline_sec: int = 2
    use_inside_quote: bool = True
    use_post_only: bool = True


@dataclass(slots=True)
class RiskConfig:
    max_daily_loss_usdt: Decimal = Decimal("30")
    max_equity_drawdown_pct: Decimal = Decimal("5.0")
    max_net_position_notional_pct: Decimal = Decimal("80.0")
    max_abs_position_units: Decimal | None = None
    min_free_margin_pct: Decimal = Decimal("20.0")
    max_stale_market_data_ms: int = 2500
    max_ws_silence_ms: int = 5000
    cancel_bot_orders_on_shutdown: bool = True
    cancel_bot_orders_on_stale_data: bool = True
    cancel_bot_orders_on_edge_loss: bool = True
    cancel_bot_orders_on_daily_loss: bool = True


@dataclass(slots=True)
class StateConfig:
    sqlite_path: str = "./state/hibachi_bot.sqlite"


@dataclass(slots=True)
class LoggingConfig:
    audit_log_path: str = "./logs/audit.jsonl"


@dataclass(slots=True)
class BotConfig:
    exchange: ExchangeConfig
    strategy: StrategyConfig
    risk: RiskConfig
    state: StateConfig
    logging: LoggingConfig
    strategy_instance_id: str = "default"


def _to_decimal_dict(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in raw.items():
        if isinstance(v, str):
            try:
                out[k] = Decimal(v)
                continue
            except Exception:
                pass
        out[k] = v
    return out


def load_config(path: str | Path) -> BotConfig:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load config file") from exc

    with Path(path).open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return BotConfig(
        exchange=ExchangeConfig(**raw.get("exchange", {})),
        strategy=StrategyConfig(**_to_decimal_dict(raw.get("strategy", {}))),
        risk=RiskConfig(**_to_decimal_dict(raw.get("risk", {}))),
        state=StateConfig(**raw.get("state", {})),
        logging=LoggingConfig(**raw.get("logging", {})),
        strategy_instance_id=raw.get("strategy_instance_id", "default"),
    )
