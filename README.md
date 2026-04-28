# Hibachi Spread Capture Control Center

이 프로젝트는 Hibachi BTC/USDT-P용 spread-capture 엔진과 로컬 웹 대시보드를 함께 제공합니다.

## 핵심 경고
- 무조건 수익 전략이 아닙니다.
- single-venue maker 전략은 한쪽 체결 시 방향성 리스크가 생깁니다.
- LIVE 전 최소 24시간 dry-run-ui로 상태/경고/로그를 검증하세요.

## 화면에서 확인 가능한 것
처음 접속(`http://127.0.0.1:8787/dashboard`)하면 다음이 보여야 합니다.
- Engine 상태(STARTING/RUNNING/ERROR/HALTED), 모드 배지(INSPECT/DRY RUN/LIVE)
- Account/Risk/Market 요약 카드
- Equity/Price 차트
- Open Orders, Events 패널

## 설치
```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
cp config.example.yaml config.local.yaml
pytest -q
```

## 명령어
- inspect: `python -m hibachi_mm.main inspect --config config.local.yaml`
- security-check: `python -m hibachi_mm.main security-check --config config.local.yaml`
- dry-run engine only: `python -m hibachi_mm.main dry-run --config config.local.yaml`
- live engine only: `python -m hibachi_mm.main live --config config.local.yaml`
- dashboard only: `python -m hibachi_mm.main dashboard --config config.local.yaml`
- dry-run + dashboard: `python -m hibachi_mm.main dry-run-ui --config config.local.yaml`
- live + dashboard: `python -m hibachi_mm.main live-ui --config config.local.yaml`

## Windows PowerShell
가상환경 활성화:
```powershell
.\.venv\Scripts\Activate.ps1
```

dashboard만 실행:
```powershell
python -m hibachi_mm.main dashboard --config config.local.yaml
```

dry-run + dashboard:
```powershell
python -m hibachi_mm.main dry-run-ui --config config.local.yaml
```

live + dashboard:
```powershell
$env:HIBACHI_ENABLE_LIVE_TRADING="I_UNDERSTAND_PERP_RISK"
python -m hibachi_mm.main live-ui --config config.local.yaml
```

접속:
- `http://127.0.0.1:8787`
- `http://127.0.0.1:8787/dashboard`

## 로그/상태 파일 위치
- audit 로그: `logs/audit.jsonl`
- 콘솔 로그: `logs/live-console.log` 또는 `logs/dryrun-console.log`
- SQLite: `state/hibachi_bot.sqlite`

## dashboard가 비어 있으면
1. `security-check` 먼저 실행
2. API 키/계정/키 env 값 확인
3. `events` 패널의 error/warning 확인
4. `logs/audit.jsonl` 확인

## Live 주의사항
- 환경변수 `HIBACHI_ENABLE_LIVE_TRADING=I_UNDERSTAND_PERP_RISK` 없으면 차단됩니다.
- `maker_entry_only=true` + `emergency_taker_exit=false` 는 live 금지입니다.
