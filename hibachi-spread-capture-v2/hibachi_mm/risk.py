from dataclasses import dataclass
from decimal import Decimal
@dataclass(slots=True)
class RiskResult: allow_entry:bool; reason:str

def evaluate(cfg, market_age_ms:int, free_margin_pct:Decimal, daily_loss:Decimal, unknown_orders:int, position_notional_abs:Decimal, equity:Decimal)->RiskResult:
    if market_age_ms>cfg.max_stale_market_data_ms: return RiskResult(False,'stale_market_data')
    if free_margin_pct<cfg.min_free_margin_pct: return RiskResult(False,'free_margin_too_low')
    if daily_loss>cfg.max_daily_loss_usdt: return RiskResult(False,'daily_loss_limit')
    if unknown_orders>0: return RiskResult(False,'unknown_open_orders')
    if equity>0 and position_notional_abs>equity*cfg.max_net_position_notional_pct/Decimal('100'): return RiskResult(False,'position_too_large')
    return RiskResult(True,'ok')
