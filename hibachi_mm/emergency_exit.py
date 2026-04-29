from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from hibachi_mm.config import BotConfig
from hibachi_mm.models import Scenario


@dataclass
class ExitDecision:
    stage: str
    use_reduce_only: bool
    use_ioc: bool
    use_market: bool
    slippage_bps: Decimal
    scenario: Scenario


class EmergencyExitPolicy:
    def __init__(self, config: BotConfig):
        self.config = config

    def decide(self, adverse_move_bps: Decimal, free_margin_pct: Decimal, drawdown_pct: Decimal, liquidation_risk_pct: Decimal) -> ExitDecision:
        ep = self.config.exit_policy
        if adverse_move_bps >= ep.emergency_trigger_adverse_bps or free_margin_pct <= ep.emergency_trigger_free_margin_pct or drawdown_pct >= ep.emergency_trigger_drawdown_pct or liquidation_risk_pct >= ep.emergency_trigger_liquidation_risk_pct:
            return ExitDecision("EMERGENCY", True, ep.emergency_reduce_only_ioc, ep.emergency_market_close, ep.max_emergency_exit_slippage_bps, Scenario.ONE_SIDE_FILLED_ADVERSE_HARD)
        if adverse_move_bps >= self.config.inventory.adverse_move_soft_bps:
            return ExitDecision("AGGRESSIVE_LIMIT", True, False, False, ep.aggressive_limit_slippage_bps, Scenario.ONE_SIDE_FILLED_ADVERSE_SOFT)
        return ExitDecision("PASSIVE_ALO", True, False, False, Decimal("0"), Scenario.ONE_SIDE_FILLED_PASSIVE_REBALANCE)
