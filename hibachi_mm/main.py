import argparse, os
from .config import load_config, load_env_credentials
from .exchange import ExchangeAdapter
from .engine import Engine
from .audit import AuditLogger


def build_client(cfg):
    creds = load_env_credentials(cfg.exchange.environment)
    if not (creds['api_key'] and creds['private_key'] and creds['account_id']):
        raise SystemExit('missing hibachi credentials in .env')
    try:
        from hibachi_xyz import HibachiApiClient
    except Exception as e:
        raise SystemExit(f'hibachi sdk missing: {e}')
    return HibachiApiClient(api_url=creds['api_url'], data_api_url=creds['data_api_url'], api_key=creds['api_key'], account_id=creds['account_id'], private_key=creds['private_key'])


def require_live_gate():
    if os.getenv('HIBACHI_ENABLE_LIVE_TRADING') != 'I_UNDERSTAND_PERP_RISK':
        raise SystemExit('live gate blocked')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['inspect','security-check','dry-run','live','dashboard','dry-run-ui','live-ui'])
    p.add_argument('--config', required=True)
    args = p.parse_args()
    cfg = load_config(args.config)
    if args.command in {'live','live-ui'}: require_live_gate()
    client = build_client(cfg)
    ex = ExchangeAdapter(client)
    if args.command == 'inspect':
        m = ex.fetch_market(cfg.exchange.symbol)
        a = ex.fetch_account()
        print({'symbol': cfg.exchange.symbol, **m, **a})
        return
    if args.command == 'security-check':
        _ = ex.fetch_market(cfg.exchange.symbol); _ = ex.fetch_account(); print('ok'); return
    mode = 'live' if args.command.startswith('live') else 'dry-run'
    engine = Engine(ex, cfg, AuditLogger(cfg.logging.audit_log_path), mode=mode)
    engine.run_forever(interval_ms=1000)

if __name__ == '__main__':
    main()
