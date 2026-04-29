from dataclasses import dataclass

@dataclass
class ExchangeConfig:
    venue: str = 'hibachi'
    environment: str = 'production'
    symbol: str = 'BTC/USDT-P'
    dedicated_subaccount_confirmed: bool = False
    allow_unknown_open_orders: bool = False

@dataclass
class StrategyConfig:
    min_gross_spread_ticks: int = 1
    use_inside_quote: bool = False
    inside_quote_min_spread_ticks: int = 3
    min_expected_edge_bps: float = 0.02
    maker_fee_bps_override: float = 0.0
    latency_cost_bps: float = 0.02
    adverse_selection_min_bps: float = 0.05
    take_profit_ticks: int = 1
    max_active_orders_per_side: int = 1

@dataclass
class RiskConfig:
    min_free_margin_pct: float = 35.0
    max_stale_market_data_ms: int = 2500

@dataclass
class AppConfig:
    exchange: ExchangeConfig
    strategy: StrategyConfig
    risk: RiskConfig

def load_config(_path:str)->AppConfig:
    return AppConfig(exchange=ExchangeConfig(), strategy=StrategyConfig(), risk=RiskConfig())
