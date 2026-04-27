from hibachi_mm.security import run_security_checks
from test_strategy import make_config


def test_security_live_requires_ack(monkeypatch):
    cfg = make_config()
    monkeypatch.delenv("HIBACHI_ENABLE_LIVE_TRADING", raising=False)
    out = run_security_checks(cfg, mode="live")
    assert any("HIBACHI_ENABLE_LIVE_TRADING" in e for e in out.errors)


def test_security_blocks_missing_live_credentials(monkeypatch):
    cfg = make_config()
    monkeypatch.setenv("HIBACHI_ENABLE_LIVE_TRADING", "I_UNDERSTAND_PERP_RISK")
    out = run_security_checks(cfg, mode="live")
    assert len(out.errors) >= 1
