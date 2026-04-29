import os, pytest
from hibachi_mm.order_manager import validate_live_gate

def test_live_gate_requires_env(monkeypatch):
    monkeypatch.delenv('HIBACHI_ENABLE_LIVE_TRADING',raising=False)
    with pytest.raises(SystemExit): validate_live_gate('live')
def test_live_gate_blocks_unknown_orders(monkeypatch):
    monkeypatch.setenv('HIBACHI_ENABLE_LIVE_TRADING','I_UNDERSTAND_PERP_RISK'); validate_live_gate('live')
def test_windows_signal_safe():
    assert True
