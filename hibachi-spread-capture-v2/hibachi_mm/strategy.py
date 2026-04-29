from decimal import Decimal
from hibachi_mm.decimal_math import bps, clamp, floor_to_step
from hibachi_mm.models import QuoteDecision

def decide(cfg, market, account, initial_margin_rate:Decimal, min_order_size:Decimal=Decimal('0.001'), min_notional:Decimal=Decimal('10'), step_size:Decimal=Decimal('0.001')):
    bid=market.best_bid; ask=market.best_ask; mid=market.mid
    cb=bid+Decimal('0.1') if cfg.use_inside_quote and bid+Decimal('0.1')<ask else bid
    ca=ask-Decimal('0.1') if cfg.use_inside_quote and ask-Decimal('0.1')>bid else ask
    if cb>=ask or ca<=bid or cb>=ca: return QuoteDecision(False,False,None,None,None,None,Decimal('0'),Decimal('1'),'crossed')
    net= bps(ca-cb,mid) - (account.maker_fee_rate*Decimal('20000')+cfg.latency_buffer_bps+cfg.adverse_selection_buffer_bps+cfg.funding_buffer_bps+cfg.mark_deviation_buffer_bps)
    if net<cfg.min_net_edge_bps: return QuoteDecision(False,False,None,None,None,None,net,Decimal('1'),'edge_below_threshold')
    edge=clamp(Decimal('1')+max(Decimal('0'),net-cfg.min_net_edge_bps)/cfg.edge_size_ramp_bps,Decimal('1'),cfg.max_edge_size_multiplier)
    dev=(account.current_position_qty*mid - account.equity*cfg.target_position_notional_pct/Decimal('100'))/account.equity if account.equity>0 else Decimal('0')
    bm=clamp(Decimal('1')-dev*cfg.position_skew_strength,cfg.min_side_size_multiplier,cfg.max_side_size_multiplier)
    am=clamp(Decimal('1')+dev*cfg.position_skew_strength,cfg.min_side_size_multiplier,cfg.max_side_size_multiplier)
    base=account.equity*cfg.entry_margin_pct/Decimal('100')/initial_margin_rate
    cap_margin=min(account.equity*cfg.max_order_margin_pct/Decimal('100'),account.free_margin*Decimal('0.5'))/initial_margin_rate
    n=min(base,cfg.max_order_notional_usdt,cap_margin)
    bq=floor_to_step((n*edge*bm)/cb,step_size); aq=floor_to_step((n*edge*am)/ca,step_size)
    sb=bq>=min_order_size and cb*bq>=min_notional; sa=aq>=min_order_size and ca*aq>=min_notional
    return QuoteDecision(sb,sa,cb,ca,bq,aq,net,edge,'ok' if (sb or sa) else 'size_filtered')
