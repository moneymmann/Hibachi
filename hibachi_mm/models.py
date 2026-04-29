from dataclasses import dataclass, field

@dataclass
class MarketSnapshot:
    best_bid: float
    best_ask: float
    mid: float
    spread_ticks: int
    spread_bps: float

@dataclass
class AccountSnapshot:
    equity: float
    balance: float
    free_margin: float
    free_margin_pct: float
    total_order_notional: float = 0.0
    total_position_notional: float = 0.0
    fees: dict = field(default_factory=dict)

@dataclass
class QuoteDecision:
    allow_entry: bool
    reason: str
    bid_price: float | None = None
    ask_price: float | None = None
    expected_edge_bps: float = 0.0
