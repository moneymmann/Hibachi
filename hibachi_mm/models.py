from dataclasses import dataclass
from decimal import Decimal

@dataclass
class MarketSnapshot:
    best_bid: Decimal
    best_ask: Decimal
    mid: Decimal
    tick_size: Decimal

@dataclass
class AccountSnapshot:
    equity: Decimal
    free_margin: Decimal
    position_qty: Decimal
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal

@dataclass
class QuoteDecision:
    should_quote: bool
    reason: str
    bid_price: Decimal | None = None
    ask_price: Decimal | None = None
    expected_edge_bps: Decimal = Decimal("0")
    size_qty: Decimal = Decimal("0")
