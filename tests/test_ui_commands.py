import importlib

from test_strategy import make_config


def test_dry_run_ui_invokes_runner(monkeypatch, tmp_path):
    m = importlib.import_module("hibachi_mm.main")
    called = {"v": False}

    async def fake_runner(cfg, mode, host, port):
        called["v"] = True

    monkeypatch.setattr(m, "run_engine_and_dashboard", fake_runner)
    monkeypatch.setattr(m, "load_config", lambda _: make_config())
    monkeypatch.setattr(m, "build_parser", lambda: type("P", (), {"parse_args": lambda self: type("A", (), {"command": "dry-run-ui", "config": "x", "host": "127.0.0.1", "port": 8787})()})())
    rc = m.main()
    assert rc == 0
    assert called["v"] is True


def test_live_ui_gate_blocks_without_env(monkeypatch):
    m = importlib.import_module("hibachi_mm.main")
    monkeypatch.delenv("HIBACHI_ENABLE_LIVE_TRADING", raising=False)
    monkeypatch.setattr(m, "load_config", lambda _: make_config())
    monkeypatch.setattr(m, "build_parser", lambda: type("P", (), {"parse_args": lambda self: type("A", (), {"command": "live-ui", "config": "x", "host": "127.0.0.1", "port": 8787})()})())
    rc = m.main()
    assert rc in (2, 3)
