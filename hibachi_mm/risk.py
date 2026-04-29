from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from hibachi_mm.config import RiskConfig
from hibachi_mm.decimal_math import HUNDRED, ZERO
from hibachi_mm.models import AccountState


@dataclass(slots=True)
class RiskStatus:
    allow_new_orders: bool
    reason: str
    free_margin_approx: Decimal
    free_margin_pct: Decimal


def compute_free_margin(account: AccountState, initial_margin_rate: Decimal) -> tuple[Decimal, Decimal]:
    used = (abs(account.total_position_notional) + abs(account.total_order_notional)) * initial_margin_rate
    free = max(ZERO, account.equity_usdt - used)
    pct = ZERO if account.equity_usdt <= ZERO else (free / account.equity_usdt) * HUNDRED
    return free, pct


def evaluate_risk(
    cfg: RiskConfig,
    account: AccountState,
    initial_margin_rate: Decimal,
    market_age_ms: int,
) -> RiskStatus:
    free, free_pct = compute_free_margin(account, initial_margin_rate)
    if market_age_ms > cfg.max_stale_market_data_ms:
        return RiskStatus(False, "stale_market_data", free, free_pct)
    if free_pct < cfg.min_free_margin_pct:
        return RiskStatus(False, "free_margin_too_low", free, free_pct)
    return RiskStatus(True, "ok", free, free_pct)
