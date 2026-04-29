import asyncio
from hibachi_mm.engine import TradingEngine
from hibachi_mm.config import load_config
from tests.test_exchange import StubApi
from hibachi_mm.exchange import HibachiExchange
from hibachi_mm.audit import Audit
from hibachi_mm.state import StateDB
class Cfg: pass
async def _run(mode,tmp_path):
    c=load_config('config.example.yaml'); c.logging.audit_log_path=str(tmp_path/'a.jsonl'); c.state.sqlite_path=str(tmp_path/'s.db')
    e=TradingEngine(mode,c,HibachiExchange(c.exchange,api_client=StubApi()),Audit(c.logging.audit_log_path),StateDB(c.state.sqlite_path)); await e.run(iterations=2); return c

def test_engine_writes_market_account_quote(tmp_path): asyncio.run(_run('dry-run',tmp_path)); assert (tmp_path/'a.jsonl').exists()
def test_engine_dry_run_never_places_order(tmp_path): asyncio.run(_run('dry-run',tmp_path)); assert 'order_submitted' not in (tmp_path/'a.jsonl').read_text()
