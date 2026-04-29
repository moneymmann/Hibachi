from hibachi_mm.engine import LiveGateError, validate_live_gate
from hibachi_mm.state import StateStore, reconcile_unknown_orders
from test_strategy import make_config


def test_unknown_open_orders_not_bot_owned(tmp_path):
    db = StateStore(str(tmp_path / "t.sqlite"))
    db.upsert_order({"order_id": "1", "nonce": "n1", "symbol": "BTC/USDT-P", "side": "BUY", "order_role": "ENTRY", "reduce_only": False, "price": "100", "qty": "1", "created_at_ms": 1, "updated_at_ms": 1, "status": "NEW", "strategy_instance_id": "s1"})
    unknown = reconcile_unknown_orders([{"order_id": "2", "nonce": "n2"}], db.list_open_orders())
    assert len(unknown) == 1


def test_live_gate_requires_env(monkeypatch):
    monkeypatch.delenv("HIBACHI_ENABLE_LIVE_TRADING", raising=False)
    try:
        validate_live_gate(make_config(), unknown_open_orders_count=0)
        assert False
    except LiveGateError:
        assert True


def test_live_gate_rejects_maker_only_exit(monkeypatch):
    cfg = make_config()
    cfg.exit_policy.emergency_taker_exit = False
    monkeypatch.setenv("HIBACHI_ENABLE_LIVE_TRADING", "I_UNDERSTAND_PERP_RISK")
    try:
        validate_live_gate(cfg, unknown_open_orders_count=0)
        assert False
    except LiveGateError:
        assert True

from hibachi_mm.order_manager import OrderManager


def test_cancel_all_orders_never_used_and_ack_timeout_halts_duplicates():
    om = OrderManager()
    om.on_order_ack_timeout("L1")
    assert om.can_submit("L1") is False
    assert om.cancel_all_called is False
