from decimal import Decimal
from hibachi_mm.risk import evaluate
from hibachi_mm.config import RiskCfg
def test_risk_blocks_stale(): assert not evaluate(RiskCfg(),3000,Decimal('50'),Decimal('0'),0,Decimal('0'),Decimal('1000')).allow_entry
