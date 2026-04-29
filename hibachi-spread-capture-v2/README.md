# hibachi-spread-capture-v2

Windows 실행:
cd "C:\bot\HibachiV2\hibachi-spread-capture-v2"
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
Copy-Item .env.example .env
Copy-Item config.example.yaml config.local.yaml
notepad .env
python -m pytest -q
python -m hibachi_mm.main inspect --config config.local.yaml
python -m hibachi_mm.main security-check --config config.local.yaml
python -m hibachi_mm.main dry-run-ui --config config.local.yaml

실거래:
$env:HIBACHI_ENABLE_LIVE_TRADING="I_UNDERSTAND_PERP_RISK"
python -m hibachi_mm.main live-ui --config config.local.yaml
