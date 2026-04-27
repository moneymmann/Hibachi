# Hibachi Spread Bot (BTC/USDT-P)

이 프로젝트는 **single-venue spread capture market making** 전략을 Hibachi perpetual futures에 맞춰 구현한 로컬 실행 봇입니다.

## 매우 중요한 리스크 경고
- 이 봇은 **무조건 수익을 보장하지 않습니다**.
- single-venue maker spread capture는 무위험 차익거래가 아닙니다.
- 한쪽만 체결되면 즉시 방향성 포지션 리스크가 생깁니다.
- 본 봇의 우선순위는 **생존(청산/마진콜 방지)** 입니다.
- `emergency_taker_exit=false` 구성은 실전(Live)에서 금지 수준으로 간주하세요.

## 설계 핵심
- 진입 주문: Post-Only/ALO maker-only
- 포지션 해소: reduce-only passive → aggressive limit → IOC/market close
- spread edge가 사라지면 즉시 신규 quote 중단
- stale data, ws silence, volatility shock, funding blackout, drawdown/loss 초과 시 방어 모드
- account sizing은 BTC 수량이 아니라 USDT equity/free margin/position notional 기반

## 실행 전 권장사항
1. 최소 24시간 dry-run 로그를 먼저 확인하세요.
2. dedicated subaccount 사용을 강력히 권장합니다.
3. 첫 live는 equity의 아주 작은 비율부터 시작하세요.

## 설치 및 실행
```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
cp config.example.yaml config.local.yaml
# .env에 키 입력
pytest -q
python -m hibachi_mm.main inspect --config config.local.yaml
python -m hibachi_mm.main security-check --config config.local.yaml
python -m hibachi_mm.main dry-run --config config.local.yaml
export HIBACHI_ENABLE_LIVE_TRADING=I_UNDERSTAND_PERP_RISK
python -m hibachi_mm.main live --config config.local.yaml
```

## CLI
- `python -m hibachi_mm.main inspect --config config.local.yaml`
- `python -m hibachi_mm.main security-check --config config.local.yaml`
- `python -m hibachi_mm.main dry-run --config config.local.yaml`
- `python -m hibachi_mm.main live --config config.local.yaml`

## Live Gate
Live 실행은 아래를 모두 만족해야 합니다.
- 환경변수 `HIBACHI_ENABLE_LIVE_TRADING=I_UNDERSTAND_PERP_RISK`
- maker-only exit 강제(`maker_entry_only=true` + `emergency_taker_exit=false`) 구성 금지
- `allow_unknown_open_orders=false`일 때 unknown order 존재 시 실행 금지


## 보안 실행 체크리스트
- `.env` 파일 권한을 `chmod 600 .env`로 제한하세요.
- API 키/개인키를 yaml 본문에 넣지 말고 환경변수로만 주입하세요.
- `security-check` 명령을 통과한 뒤에만 dry-run/live를 실행하세요.
