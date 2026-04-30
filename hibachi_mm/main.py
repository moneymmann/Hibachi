import argparse, asyncio, os, signal
import uvicorn
from .config import load_config
from .exchange import HibachiExchange
from .audit import AuditLogger
from .state import init_db
from .engine import TradingEngine
from .dashboard import create_app
from .dashboard_store import DashboardStore


def gate_live():
    if os.getenv('HIBACHI_ENABLE_LIVE_TRADING') != 'I_UNDERSTAND_PERP_RISK':
        raise RuntimeError('live trading gate not satisfied')

async def run_ui(cfg, dry_run: bool):
    if not dry_run: gate_live()
    store=DashboardStore(); audit=AuditLogger(cfg['logging']['audit_log_path']); init_db(cfg['state']['sqlite_path'])
    ex=HibachiExchange(cfg, os.environ)
    engine=TradingEngine(cfg,ex,audit,store,dry_run=dry_run)
    app=create_app(store)
    server=uvicorn.Server(uvicorn.Config(app,host=cfg['exchange']['dashboard_host'],port=cfg['exchange']['dashboard_port'],log_level='warning'))
    t1=asyncio.create_task(engine.run()); t2=asyncio.create_task(server.serve())
    loop=asyncio.get_running_loop()
    def stop(*_): engine.running=False
    try: loop.add_signal_handler(signal.SIGINT, stop)
    except (NotImplementedError, RuntimeError): signal.signal(signal.SIGINT, stop)
    await asyncio.gather(t1,t2)

def main():
    p=argparse.ArgumentParser(); p.add_argument('cmd'); p.add_argument('--config', required=True); a=p.parse_args(); cfg=load_config(a.config)
    if a.cmd=='inspect':
        ex=HibachiExchange(cfg, os.environ)
        async def r():
            m=await ex.get_market_snapshot(); ac=await ex.get_account_snapshot()
            print('best_bid',m.best_bid); print('best_ask',m.best_ask); print('mid',m.mid); print('equity',ac.equity); print('free_margin',ac.free_margin); print('current_position_qty',ac.position_qty); print('maker_fee_rate',ac.maker_fee_rate); print('taker_fee_rate',ac.taker_fee_rate)
        asyncio.run(r())
    elif a.cmd=='security-check':
        if not cfg['strategy']['emergency_reduce_only_exit']: raise SystemExit(2)
        print('security-check: ok')
    elif a.cmd=='dashboard':
        app=create_app(DashboardStore()); uvicorn.run(app,host=cfg['exchange']['dashboard_host'],port=cfg['exchange']['dashboard_port'])
    elif a.cmd in ('dry-run','dry-run-ui'): asyncio.run(run_ui(cfg, True))
    elif a.cmd in ('live','live-ui'): asyncio.run(run_ui(cfg, False))

if __name__=='__main__': main()
