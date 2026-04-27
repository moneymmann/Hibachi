from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass
class ExchangeConfig:
    venue: str
    environment: str
    symbol: str
    api_endpoint: str
    data_api_endpoint: str
    api_endpoint_env: str
    data_api_endpoint_env: str
    api_key_env: str
    account_id_env: str
    private_key_env: str
    public_key_env: str
    dedicated_subaccount_confirmed: bool = False
    allow_unknown_open_orders: bool = False


@dataclass
class StrategyConfig:
    mode: str
    sizing_mode: str
    entry_margin_pct: Decimal
    max_order_margin_pct: Decimal
    max_total_leverage: Decimal
    max_order_notional_usdt: Decimal
    min_net_edge_bps: Decimal
    edge_size_ramp_bps: Decimal
    max_edge_size_multiplier: Decimal
    top_depth_levels_for_cap: int
    top_liquidity_participation_pct: Decimal
    target_position_notional_pct: Decimal
    position_skew_strength: Decimal
    min_side_size_multiplier: Decimal
    max_side_size_multiplier: Decimal
    latency_buffer_bps: Decimal
    adverse_selection_buffer_bps: Decimal
    funding_buffer_bps: Decimal
    mark_deviation_buffer_bps: Decimal
    volatility_buffer_min_bps: Decimal
    volatility_buffer_max_bps: Decimal
    quote_interval_ms: int
    quote_ttl_ms: int
    min_reprice_ticks: int
    creation_deadline_sec: int
    use_inside_quote: bool
    use_post_only: bool
    cancel_on_edge_loss: bool


@dataclass
class InventoryConfig:
    max_net_position_notional_pct: Decimal
    inventory_resolution_threshold_pct: Decimal
    maker_rebalance_grace_ms: int
    adverse_move_soft_bps: Decimal
    adverse_move_hard_bps: Decimal
    flat_position_threshold_pct: Decimal


@dataclass
class ExitPolicyConfig:
    maker_entry_only: bool
    emergency_taker_exit: bool
    passive_reduce_only_alo: bool
    passive_exit_timeout_ms: int
    aggressive_reduce_only_limit: bool
    aggressive_limit_slippage_bps: Decimal
    aggressive_exit_timeout_ms: int
    emergency_reduce_only_ioc: bool
    emergency_market_close: bool
    emergency_trigger_adverse_bps: Decimal
    emergency_trigger_drawdown_pct: Decimal
    emergency_trigger_free_margin_pct: Decimal
    emergency_trigger_liquidation_risk_pct: Decimal
    max_emergency_exit_slippage_bps: Decimal


@dataclass
class RiskConfig:
    max_daily_loss_usdt: Decimal
    max_equity_drawdown_pct: Decimal
    min_free_margin_pct: Decimal
    max_stale_market_data_ms: int
    max_ws_silence_ms: int
    max_order_ack_ms: int
    max_cancel_ack_ms: int
    max_1s_mid_move_bps: Decimal
    max_5s_mid_move_bps: Decimal
    max_spread_bps_for_normal_mode: Decimal
    min_depth_usdt_for_quote: Decimal
    funding_blackout_before_sec: int
    funding_blackout_after_sec: int
    max_abs_predicted_funding_bps: Decimal
    cancel_bot_orders_on_shutdown: bool
    cancel_bot_orders_on_stale_data: bool
    cancel_bot_orders_on_edge_loss: bool
    cancel_bot_orders_on_daily_loss: bool


@dataclass
class StateConfig:
    sqlite_path: str


@dataclass
class LoggingConfig:
    audit_log_path: str


@dataclass
class BotConfig:
    exchange: ExchangeConfig
    strategy: StrategyConfig
    inventory: InventoryConfig
    exit_policy: ExitPolicyConfig
    risk: RiskConfig
    state: StateConfig
    logging: LoggingConfig

    @classmethod
    def model_validate(cls, data: dict) -> "BotConfig":
        def dec_fields(d: dict, keys: list[str]) -> None:
            for k in keys:
                d[k] = Decimal(str(d[k]))

        s = dict(data["strategy"])
        s.setdefault("mode", "adaptive_market_making")
        s.setdefault("sizing_mode", "equity_percent_margin")
        dec_fields(s, ["entry_margin_pct", "max_order_margin_pct", "max_total_leverage", "max_order_notional_usdt", "min_net_edge_bps", "edge_size_ramp_bps", "max_edge_size_multiplier", "top_liquidity_participation_pct", "target_position_notional_pct", "position_skew_strength", "min_side_size_multiplier", "max_side_size_multiplier", "latency_buffer_bps", "adverse_selection_buffer_bps", "funding_buffer_bps", "mark_deviation_buffer_bps", "volatility_buffer_min_bps", "volatility_buffer_max_bps"])

        i = dict(data["inventory"])
        dec_fields(i, ["max_net_position_notional_pct", "inventory_resolution_threshold_pct", "adverse_move_soft_bps", "adverse_move_hard_bps", "flat_position_threshold_pct"])

        e = dict(data["exit_policy"])
        dec_fields(e, ["aggressive_limit_slippage_bps", "emergency_trigger_adverse_bps", "emergency_trigger_drawdown_pct", "emergency_trigger_free_margin_pct", "emergency_trigger_liquidation_risk_pct", "max_emergency_exit_slippage_bps"])

        r = dict(data["risk"])
        dec_fields(r, ["max_daily_loss_usdt", "max_equity_drawdown_pct", "min_free_margin_pct", "max_1s_mid_move_bps", "max_5s_mid_move_bps", "max_spread_bps_for_normal_mode", "min_depth_usdt_for_quote", "max_abs_predicted_funding_bps"])

        return cls(
            exchange=ExchangeConfig(**data["exchange"]),
            strategy=StrategyConfig(**s),
            inventory=InventoryConfig(**i),
            exit_policy=ExitPolicyConfig(**e),
            risk=RiskConfig(**r),
            state=StateConfig(**data["state"]),
            logging=LoggingConfig(**data["logging"]),
        )


def load_config(path: str | Path) -> BotConfig:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return BotConfig.model_validate(data)
