import os, pytest
from hibachi_mm.main import gate_live

def test_live_gate_requires_env(monkeypatch):
    monkeypatch.delenv('HIBACHI_ENABLE_LIVE_TRADING', raising=False)
    with pytest.raises(RuntimeError): gate_live()
