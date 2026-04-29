from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


@dataclass
class Level:
    price: Decimal
    qty: Decimal


@dataclass
class MarketSnapshot:
    symbol: str
    best_bid_price: Decimal
    best_bid_qty: Decimal
    best_ask_price: Decimal
    best_ask_qty: Decimal
    orderbook_bids: list[Level]
    orderbook_asks: list[Level]
    mid: Decimal
    mark_price: Decimal | None
    spot_price: Decimal | None
    last_trade_price: Decimal | None
    predicted_funding_rate: Decimal | None
    ts_ms: int


@dataclass
class AccountState:
    equity_usdt: Decimal
    account_balance: Decimal
    total_unrealized_pnl: Decimal
    total_order_notional: Decimal
    total_position_notional: Decimal
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal
    current_position_qty_signed: Decimal
    current_position_notional_signed: Decimal
    free_margin_approx: Decimal
    free_margin_pct: Decimal
    total_leverage_approx: Decimal
    liquidation_risk_pct_approx: Decimal
    pending_bot_orders: list[dict] = field(default_factory=list)
    pending_unknown_orders: list[dict] = field(default_factory=list)


@dataclass
class ContractRules:
    symbol: str
    tick_size: Decimal
    step_size: Decimal
    min_order_size: Decimal
    min_notional: Decimal
    initial_margin_rate: Decimal
    maintenance_margin_rate: Decimal
    status: str


class Scenario(str, Enum):
    NORMAL_QUOTING = "NORMAL_QUOTING"
    EDGE_GONE = "EDGE_GONE"
    POST_ONLY_REJECT = "POST_ONLY_REJECT"
    BOTH_SIDES_FILLED = "BOTH_SIDES_FILLED"
    ONE_SIDE_FILLED_PASSIVE_REBALANCE = "ONE_SIDE_FILLED_PASSIVE_REBALANCE"
    ONE_SIDE_FILLED_ADVERSE_SOFT = "ONE_SIDE_FILLED_ADVERSE_SOFT"
    ONE_SIDE_FILLED_ADVERSE_HARD = "ONE_SIDE_FILLED_ADVERSE_HARD"
    INVENTORY_RESOLUTION = "INVENTORY_RESOLUTION"
    VOLATILITY_SHOCK = "VOLATILITY_SHOCK"
    FUNDING_BLACKOUT = "FUNDING_BLACKOUT"
    MARK_INDEX_DIVERGENCE = "MARK_INDEX_DIVERGENCE"
    LOW_DEPTH = "LOW_DEPTH"
    STALE_DATA = "STALE_DATA"
    WS_DISCONNECTED = "WS_DISCONNECTED"
    ORDER_ACK_TIMEOUT = "ORDER_ACK_TIMEOUT"
    CANCEL_ACK_TIMEOUT = "CANCEL_ACK_TIMEOUT"
    RATE_LIMIT_RISK = "RATE_LIMIT_RISK"
    UNKNOWN_OPEN_ORDERS = "UNKNOWN_OPEN_ORDERS"
    DAILY_LOSS_HALT = "DAILY_LOSS_HALT"
    DRAWDOWN_HALT = "DRAWDOWN_HALT"
    LIQUIDATION_RISK_HALT = "LIQUIDATION_RISK_HALT"
    MAINTENANCE_HALT = "MAINTENANCE_HALT"


@dataclass
class QuoteDecision:
    mode: str
    should_bid: bool
    should_ask: bool
    bid_price: Decimal | None
    bid_qty: Decimal | None
    ask_price: Decimal | None
    ask_qty: Decimal | None
    mid: Decimal
    gross_spread_bps: Decimal
    net_edge_bps: Decimal
    edge_size_multiplier: Decimal
    bid_position_multiplier: Decimal
    ask_position_multiplier: Decimal
    bid_notional_usdt: Decimal
    ask_notional_usdt: Decimal
    reason: str
