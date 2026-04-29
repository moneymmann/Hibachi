from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(slots=True)
class Level:
    price: Decimal
    qty: Decimal


@dataclass(slots=True)
class MarketSnapshot:
    symbol: str
    best_bid_price: Decimal
    best_bid_qty: Decimal
    best_ask_price: Decimal
    best_ask_qty: Decimal
    orderbook_bids: list[Level]
    orderbook_asks: list[Level]
    mark_price: Decimal | None
    spot_price: Decimal | None
    funding_rate_estimation: Decimal | None
    ts_ms: int


@dataclass(slots=True)
class ContractRules:
    symbol: str
    tick_size: Decimal
    step_size: Decimal
    min_order_size: Decimal
    min_notional: Decimal
    initial_margin_rate: Decimal
    maintenance_margin_rate: Decimal
    settlement_symbol: str
    underlying_symbol: str
    orderbook_granularities: list[str]
    status: str


@dataclass(slots=True)
class AccountState:
    equity_usdt: Decimal
    account_balance: Decimal
    total_unrealized_pnl: Decimal
    total_order_notional: Decimal
    total_position_notional: Decimal
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal
    positions: list[dict]
    current_symbol_position_qty: Decimal
    current_symbol_position_notional_signed: Decimal
    pending_bot_orders: list[dict] = field(default_factory=list)
    pending_unknown_orders: list[dict] = field(default_factory=list)


@dataclass(slots=True)
class QuoteDecision:
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
    bid_margin_budget_usdt: Decimal
    ask_margin_budget_usdt: Decimal
    bid_notional_usdt: Decimal
    ask_notional_usdt: Decimal
    projected_long_notional: Decimal
    projected_short_notional: Decimal
    reason: str
