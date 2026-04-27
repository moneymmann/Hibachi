from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from hibachi_mm.config import BotConfig
from hibachi_mm.decimal_math import BPS, D
from hibachi_mm.models import AccountState, MarketSnapshot, Scenario


@dataclass
class RiskResult:
    allowed: bool
    scenario: Scenario
    reason: str


class RiskEngine:
    def __init__(self, config: BotConfig):
        self.config = config

    def evaluate_market_health(self, market: MarketSnapshot, now_ms: int, ws_silence_ms: int, move_1s_bps: Decimal, move_5s_bps: Decimal) -> RiskResult:
        rcfg = self.config.risk
        age = now_ms - market.ts_ms
        if age > rcfg.max_stale_market_data_ms:
            return RiskResult(False, Scenario.STALE_DATA, "stale market data")
        if ws_silence_ms > rcfg.max_ws_silence_ms:
            return RiskResult(False, Scenario.WS_DISCONNECTED, "ws disconnected")
        if abs(move_1s_bps) > rcfg.max_1s_mid_move_bps or abs(move_5s_bps) > rcfg.max_5s_mid_move_bps:
            return RiskResult(False, Scenario.VOLATILITY_SHOCK, "volatility shock")
        return RiskResult(True, Scenario.NORMAL_QUOTING, "ok")

    def evaluate_account_limits(self, account: AccountState, daily_pnl: Decimal, max_equity_seen: Decimal) -> RiskResult:
        rcfg = self.config.risk
        if daily_pnl <= -abs(rcfg.max_daily_loss_usdt):
            return RiskResult(False, Scenario.DAILY_LOSS_HALT, "daily loss exceeded")
        drawdown_pct = D("0") if max_equity_seen == 0 else (max_equity_seen - account.equity_usdt) / max_equity_seen * D("100")
        if drawdown_pct > rcfg.max_equity_drawdown_pct:
            return RiskResult(False, Scenario.DRAWDOWN_HALT, "drawdown exceeded")
        if account.free_margin_pct < rcfg.min_free_margin_pct or account.liquidation_risk_pct_approx > self.config.exit_policy.emergency_trigger_liquidation_risk_pct:
            return RiskResult(False, Scenario.LIQUIDATION_RISK_HALT, "liquidation risk")
        return RiskResult(True, Scenario.NORMAL_QUOTING, "ok")

    def mark_index_divergence_bps(self, market: MarketSnapshot) -> Decimal:
        if market.mark_price is None or market.mid == 0:
            return D("0")
        return abs((market.mid - market.mark_price) / market.mid) * BPS
