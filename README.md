# hibachi-spread-capture-pro

Hibachi BTC/USDT-P spread capture / market making bot skeleton for Windows (Python 3.13).

## Run (PowerShell)
```powershell
cd "C:\bot\Hibachi"
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
Copy-Item .env.example .env
Copy-Item config.example.yaml config.local.yaml
python -m pytest -q
python -m hibachi_mm.main inspect --config config.local.yaml
python -m hibachi_mm.main security-check --config config.local.yaml
python -m hibachi_mm.main dry-run-ui --config config.local.yaml
```

## Live
```powershell
$env:HIBACHI_ENABLE_LIVE_TRADING="I_UNDERSTAND_PERP_RISK"
python -m hibachi_mm.main live-ui --config config.local.yaml
```
