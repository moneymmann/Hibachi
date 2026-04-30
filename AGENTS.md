# AGENT RULES
1. Runtime에서는 fake/stub data 사용 금지.
2. Tests에서만 StubExchange/StubApi 허용.
3. .env, .venv, logs, state, *.sqlite, *.jsonl, *.pyc, 이미지, zip, 바이너리 파일 commit 금지.
4. 내부 계산은 Decimal 사용. float는 SDK boundary 또는 UI 표시용으로만 허용.
5. Windows PowerShell 호환 필수.
6. live/live-ui는 HIBACHI_ENABLE_LIVE_TRADING=I_UNDERSTAND_PERP_RISK 없으면 반드시 차단.
7. 모든 기능은 pytest와 실제 CLI acceptance로 검증한다.
8. Codex가 모르는 부분은 임의 stub으로 넘기지 말고 실제 SDK 문서를 기준으로 adapter를 방어적으로 구현한다.
