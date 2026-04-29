from pathlib import Path
from types import SimpleNamespace
from hibachi_mm.engine import Engine
from hibachi_mm.audit import AuditLogger
from hibachi_mm.config import AppConfig, ExchangeConfig, StrategyConfig, RiskConfig, LoggingConfig

class StubExchange:
    def fetch_market(self, _): return {'best_bid':60000.0,'best_ask':60001.0,'mid':60000.5,'bid_qty':1,'ask_qty':1}
    def fetch_account(self): return {'equity':123.0,'total_order_notional':0.0,'total_position_notional':0.0,'fees':{}}

def test_audit_jsonl_created_and_events_written(tmp_path):
    p = tmp_path/'audit.jsonl'
    cfg=AppConfig(ExchangeConfig(),StrategyConfig(min_expected_edge_bps=-1),RiskConfig(),LoggingConfig(str(p)))
    e=Engine(StubExchange(),cfg,AuditLogger(str(p)),'dry-run')
    e.step()
    text = Path(p).read_text(encoding='utf-8')
    assert 'market_snapshot' in text and 'account_snapshot' in text and 'quote_decision' in text
