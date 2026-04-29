from dataclasses import dataclass, field
from decimal import Decimal
@dataclass(slots=True)
class Level: price: Decimal; qty: Decimal
@dataclass(slots=True)
class MarketSnapshot:
    symbol:str; best_bid:Decimal; best_ask:Decimal; best_bid_qty:Decimal; best_ask_qty:Decimal
    bids:list[Level]; asks:list[Level]; mid:Decimal; spread_bps:Decimal; ts_ms:int
@dataclass(slots=True)
class AccountSnapshot:
    equity:Decimal; balance:Decimal; unrealized_pnl:Decimal; total_order_notional:Decimal; total_position_notional:Decimal
    current_position_qty:Decimal; maker_fee_rate:Decimal; taker_fee_rate:Decimal; free_margin:Decimal; free_margin_pct:Decimal
    pending_bot_orders:list[dict]=field(default_factory=list); pending_unknown_orders:list[dict]=field(default_factory=list)
@dataclass(slots=True)
class QuoteDecision:
    should_bid:bool; should_ask:bool; bid_price:Decimal|None; ask_price:Decimal|None; bid_qty:Decimal|None; ask_qty:Decimal|None
    net_edge_bps:Decimal; edge_mult:Decimal; reason:str
