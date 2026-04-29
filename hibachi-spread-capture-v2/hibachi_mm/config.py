from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

@dataclass(slots=True)
class ExchangeCfg: venue:str='hibachi'; environment:str='production'; symbol:str='BTC/USDT-P'; dedicated_subaccount_confirmed:bool=False; allow_unknown_open_orders:bool=False
@dataclass(slots=True)
class StrategyCfg:
    sizing_mode:str='equity_percent_margin'; entry_margin_pct:Decimal=Decimal('1'); max_order_margin_pct:Decimal=Decimal('3'); max_total_leverage:Decimal=Decimal('1')
    max_order_notional_usdt:Decimal=Decimal('999999'); min_net_edge_bps:Decimal=Decimal('1.5'); edge_size_ramp_bps:Decimal=Decimal('4'); max_edge_size_multiplier:Decimal=Decimal('3')
    top_depth_levels_for_cap:int=3; top_liquidity_participation_pct:Decimal=Decimal('20'); target_position_notional_pct:Decimal=Decimal('0'); position_skew_strength:Decimal=Decimal('2')
    min_side_size_multiplier:Decimal=Decimal('0.1'); max_side_size_multiplier:Decimal=Decimal('2.5'); latency_buffer_bps:Decimal=Decimal('0.8'); adverse_selection_buffer_bps:Decimal=Decimal('2'); funding_buffer_bps:Decimal=Decimal('0.7'); mark_deviation_buffer_bps:Decimal=Decimal('0.7')
    quote_interval_ms:int=500; quote_ttl_ms:int=2500; min_reprice_ticks:int=1; use_post_only:bool=True; use_inside_quote:bool=True
@dataclass(slots=True)
class ExitPolicyCfg: maker_entry_only:bool=True; emergency_taker_exit:bool=True; passive_reduce_only_alo:bool=True; aggressive_reduce_only_limit:bool=True; emergency_reduce_only_ioc:bool=True; emergency_market_close:bool=True; maker_rebalance_grace_ms:int=1200; adverse_move_soft_bps:Decimal=Decimal('4'); adverse_move_hard_bps:Decimal=Decimal('8')
@dataclass(slots=True)
class RiskCfg: max_daily_loss_usdt:Decimal=Decimal('10'); max_equity_drawdown_pct:Decimal=Decimal('2'); max_net_position_notional_pct:Decimal=Decimal('40'); min_free_margin_pct:Decimal=Decimal('25'); max_stale_market_data_ms:int=2500; max_ws_silence_ms:int=5000; max_1s_mid_move_bps:Decimal=Decimal('8'); max_5s_mid_move_bps:Decimal=Decimal('18'); min_depth_usdt_for_quote:Decimal=Decimal('1000')
@dataclass(slots=True)
class StateCfg: sqlite_path:str='./state/hibachi_bot.sqlite'
@dataclass(slots=True)
class LoggingCfg: audit_log_path:str='./logs/audit.jsonl'
@dataclass(slots=True)
class BotConfig: exchange:ExchangeCfg; strategy:StrategyCfg; exit_policy:ExitPolicyCfg; risk:RiskCfg; state:StateCfg; logging:LoggingCfg

def _dct(d):
    out={}
    for k,v in d.items():
        if isinstance(v,str):
            try: out[k]=Decimal(v); continue
            except Exception: pass
        out[k]=v
    return out

def load_config(path:str)->BotConfig:
    raw={}
    try:
        import yaml
        raw=yaml.safe_load(Path(path).read_text()) or {}
    except Exception:
        return BotConfig(ExchangeCfg(),StrategyCfg(),ExitPolicyCfg(),RiskCfg(),StateCfg(),LoggingCfg())
    return BotConfig(ExchangeCfg(**raw.get('exchange',{})),StrategyCfg(**_dct(raw.get('strategy',{}))),ExitPolicyCfg(**_dct(raw.get('exit_policy',{}))),RiskCfg(**_dct(raw.get('risk',{}))),StateCfg(**raw.get('state',{})),LoggingCfg(**raw.get('logging',{})))
