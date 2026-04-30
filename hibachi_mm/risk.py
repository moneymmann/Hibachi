from decimal import Decimal

def evaluate_risk(cfg, market, account, unknown_orders=0):
    min_free=Decimal(str(cfg['risk']['min_free_margin_pct']))
    free_pct=(account.free_margin/account.equity*Decimal('100')) if account.equity>0 else Decimal('0')
    ok=free_pct>=min_free and unknown_orders==0
    return {"ok":ok, "free_margin_pct":str(free_pct), "unknown_orders":unknown_orders}
