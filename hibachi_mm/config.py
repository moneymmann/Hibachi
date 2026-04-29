from dataclasses import dataclass
from pathlib import Path
import os


def _parse_scalar(v: str):
    t=v.strip()
    if t.lower() in {"true","false"}: return t.lower()=="true"
    if t.startswith('"') and t.endswith('"'): t=t[1:-1]
    try:
        if '.' in t: return float(t)
        return int(t)
    except ValueError:
        return t


def _tiny_yaml(path: str)->dict:
    data, section = {}, None
    for raw in Path(path).read_text(encoding='utf-8').splitlines():
        if not raw.strip() or raw.strip().startswith('#'): continue
        if not raw.startswith(' '):
            section = raw.split(':',1)[0].strip(); data[section]={}; continue
        k,v = raw.strip().split(':',1)
        data[section][k.strip()] = _parse_scalar(v)
    return data

@dataclass
class ExchangeConfig:
    venue: str='hibachi'; environment: str='production'; symbol: str='BTC/USDT-P'; dedicated_subaccount_confirmed: bool=False; allow_unknown_open_orders: bool=False

@dataclass
class StrategyConfig:
    min_gross_spread_ticks:int=1; use_inside_quote:bool=False; inside_quote_min_spread_ticks:int=3; min_expected_edge_bps:float=0.02; maker_fee_bps_override:float=0.0; latency_cost_bps:float=0.02; adverse_selection_min_bps:float=0.05; take_profit_ticks:int=1; max_active_orders_per_side:int=1

@dataclass
class RiskConfig:
    min_free_margin_pct:float=35.0; max_stale_market_data_ms:int=2500

@dataclass
class LoggingConfig:
    audit_log_path:str='./logs/audit.jsonl'

@dataclass
class AppConfig:
    exchange:ExchangeConfig; strategy:StrategyConfig; risk:RiskConfig; logging:LoggingConfig

def load_config(path:str)->AppConfig:
    raw=_tiny_yaml(path)
    return AppConfig(ExchangeConfig(**raw.get('exchange',{})), StrategyConfig(**raw.get('strategy',{})), RiskConfig(**raw.get('risk',{})), LoggingConfig(**raw.get('logging',{})))

def load_env_credentials(environment='production'):
    suffix = '_PRODUCTION' if environment=='production' else ''
    return {
        'api_url': os.getenv(f'HIBACHI_API_ENDPOINT{suffix}', os.getenv('HIBACHI_API_ENDPOINT','https://api.hibachi.xyz')),
        'data_api_url': os.getenv(f'HIBACHI_DATA_API_ENDPOINT{suffix}', os.getenv('HIBACHI_DATA_API_ENDPOINT','https://data-api.hibachi.xyz')),
        'api_key': os.getenv(f'HIBACHI_API_KEY{suffix}') or os.getenv('HIBACHI_API_KEY'),
        'private_key': os.getenv(f'HIBACHI_PRIVATE_KEY{suffix}') or os.getenv('HIBACHI_PRIVATE_KEY'),
        'account_id': os.getenv(f'HIBACHI_ACCOUNT_ID{suffix}') or os.getenv('HIBACHI_ACCOUNT_ID'),
    }
