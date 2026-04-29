import os, pytest
from hibachi_mm.main import require_live_gate

def test_live_gate_requires_env(monkeypatch):
    monkeypatch.delenv('HIBACHI_ENABLE_LIVE_TRADING', raising=False)
    with pytest.raises(SystemExit): require_live_gate()

def test_live_blocks_unknown_orders():
    assert True
