import argparse, anyio, signal
from hibachi_mm.config import load_config
from hibachi_mm.exchange import HibachiExchange
from hibachi_mm.audit import Audit
from hibachi_mm.state import StateDB
from hibachi_mm.engine import TradingEngine
from hibachi_mm.order_manager import validate_live_gate
from hibachi_mm.dashboard import build_dashboard_app
from hibachi_mm.dashboard_store import DashboardStore

def install_signal_handlers(engine):
    def _h(*_): engine.running=False
    try: signal.signal(signal.SIGINT,_h); signal.signal(signal.SIGTERM,_h)
    except Exception: pass

def build_parser():
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['inspect','security-check','dry-run','live','dashboard','dry-run-ui','live-ui']); p.add_argument('--config',required=True); return p

async def _run(mode,cfg):
    validate_live_gate(mode)
    ex=HibachiExchange(cfg.exchange); audit=Audit(cfg.logging.audit_log_path); db=StateDB(cfg.state.sqlite_path)
    if mode=='inspect': print(ex.get_market_snapshot(cfg.exchange.symbol)); print(ex.get_account_snapshot(cfg.exchange.symbol)); return
    if mode=='security-check': print('security-check: ok'); return
    if mode in {'dashboard','dry-run-ui','live-ui'}:
        import uvicorn
        store=DashboardStore(); engine=TradingEngine('dry-run' if mode=='dry-run-ui' else ('live' if mode=='live-ui' else 'dry-run'),cfg,ex,audit,db,store)
        install_signal_handlers(engine)
        async with anyio.create_task_group() as tg:
            tg.start_soon(engine.run)
            tg.start_soon(uvicorn.Server(uvicorn.Config(build_dashboard_app(store),host='127.0.0.1',port=8787,log_level='warning')).serve)
        return
    engine=TradingEngine(mode,cfg,ex,audit,db); install_signal_handlers(engine); await engine.run()

def main():
    a=build_parser().parse_args(); cfg=load_config(a.config); anyio.run(_run,a.mode,cfg)
if __name__=='__main__': main()
