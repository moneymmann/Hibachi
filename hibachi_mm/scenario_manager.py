from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from hibachi_mm.config import BotConfig
from hibachi_mm.models import Scenario


@dataclass
class PositionEvent:
    position_qty: Decimal
    adverse_move_bps: Decimal
    elapsed_ms_since_fill: int


class ScenarioManager:
    def __init__(self, config: BotConfig):
        self.config = config
        self.post_only_reject_streak = {"BUY": 0, "SELL": 0}
        self.cooldown_until_ms = {"BUY": 0, "SELL": 0}

    def on_post_only_reject(self, side: str, now_ms: int) -> Scenario:
        self.post_only_reject_streak[side] += 1
        if self.post_only_reject_streak[side] >= 3:
            self.cooldown_until_ms[side] = now_ms + 5000
        return Scenario.POST_ONLY_REJECT

    def can_quote_side(self, side: str, now_ms: int) -> bool:
        return now_ms >= self.cooldown_until_ms[side]

    def inventory_scenario(self, event: PositionEvent) -> Scenario:
        inv = self.config.inventory
        if event.position_qty == 0:
            return Scenario.BOTH_SIDES_FILLED
        if abs(event.adverse_move_bps) >= inv.adverse_move_hard_bps:
            return Scenario.ONE_SIDE_FILLED_ADVERSE_HARD
        if abs(event.adverse_move_bps) >= inv.adverse_move_soft_bps:
            return Scenario.ONE_SIDE_FILLED_ADVERSE_SOFT
        if event.elapsed_ms_since_fill >= inv.maker_rebalance_grace_ms:
            return Scenario.ONE_SIDE_FILLED_ADVERSE_SOFT
        return Scenario.ONE_SIDE_FILLED_PASSIVE_REBALANCE
