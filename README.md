# hibachi-spread-bot

Hibachi BTC/USDT-P perpetual/futures 전용 spread-capture market-making bot입니다.

## 핵심 원칙
- SoDEX spot 구조 미사용, Hibachi cross-margin 기반.
- 주문은 **LIMIT + POST_ONLY(ALO)** 만 허용.
- Market/IOC 금지.
- 수량은 equity/free margin 기반 동적 sizing.
- long/short inventory skew 반영으로 반대 방향 quote 증대.
- unknown open order 보호(ledger 불일치 시 live halt 기본).
- cancel_all_orders 기본 금지.

## 모드
- `inspect`: 연결/메타데이터/잔고/오더북 점검만, 주문 없음.
- `dry-run`: 전략 계산 + JSONL audit 로그만 기록.
- `live`: 실주문 허용. `HIBACHI_ENABLE_LIVE_TRADING=I_UNDERSTAND_PERP_RISK` 필수.

## 실행 순서
1. `python3.13 -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -e .`
4. `cp .env.example .env`
5. `cp config.example.yaml config.local.yaml`
6. `.env`에 API key/private key/public key/account ID 입력
7. `pytest -q`
8. `python -m hibachi_mm.main inspect --config config.local.yaml`
9. `python -m hibachi_mm.main dry-run --config config.local.yaml`
10. dry-run 로그 확인
11. `export HIBACHI_ENABLE_LIVE_TRADING=I_UNDERSTAND_PERP_RISK`
12. `python -m hibachi_mm.main live --config config.local.yaml`

## CLI
- `python -m hibachi_mm.main inspect --config config.local.yaml`
- `python -m hibachi_mm.main dry-run --config config.local.yaml`
- `python -m hibachi_mm.main live --config config.local.yaml`
