# hibachi-spread-capture-pro (MVP)

이 소프트웨어는 수익을 보장하지 않습니다.

- Maker spread capture는 one-sided fill risk가 있습니다.
- 전용 서브계정을 사용하세요.
- 첫 live 실행은 작은 `max_order_notional_usdt`로 시작하세요.
- API 키는 절대 커밋하지 마세요.
- Dashboard: http://127.0.0.1:8787/dashboard
- Audit log: `logs/audit.jsonl`

## Windows PowerShell Quick Start
1. `.env` 준비
2. `scripts/RUN_SETUP.bat`
3. `scripts/RUN_DRY_RUN_UI.bat`
4. `scripts/RUN_LIVE_SMOKE.bat`
5. 검증 후 `scripts/RUN_LIVE_UI.bat`

## Troubleshooting
- Acceptance #1 (`python -m pytest -q`) 실패: Python 환경에 의존성(`PyYAML`, `fastapi`, `uvicorn`, `anyio`)이 없으면 실패.
- Acceptance #2 (`inspect`) 실패: `.env` API 키/계정 ID 누락 또는 Hibachi API 연결 실패.
- Acceptance #3/#5/#7 루프 즉시 종료: live gate/env 또는 API 예외 확인, `logs/audit.jsonl`의 `api_error` 확인.
- Acceptance #6 (`live-smoke`) 실패: live gate 미설정 또는 주문 권한/파라미터 오류.
