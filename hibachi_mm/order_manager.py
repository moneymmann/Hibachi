from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ManagedOrder:
    order_id: str
    nonce: str
    symbol: str
    side: str
    order_role: str


class OrderManager:
    def __init__(self):
        self.cancel_all_called = False
        self.pending_unknown_ack: set[str] = set()

    def cancel_bot_orders(self, bot_orders: list[ManagedOrder]) -> list[str]:
        return [o.order_id for o in bot_orders]

    def on_order_ack_timeout(self, logical_id: str) -> None:
        self.pending_unknown_ack.add(logical_id)

    def can_submit(self, logical_id: str) -> bool:
        return logical_id not in self.pending_unknown_ack
