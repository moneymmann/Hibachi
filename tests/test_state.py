from hibachi_mm.state import Ledger


def test_unknown_open_order_not_bot_owned(tmp_path):
    ledger = Ledger(str(tmp_path / "s.db"))
    ledger.upsert_order(
        {
            "order_id": "known-1",
            "nonce": "n1",
            "symbol": "BTC/USDT-P",
            "side": "BID",
            "price": "100",
            "qty": "1",
            "created_at_ms": 1,
            "updated_at_ms": 1,
            "status": "OPEN",
            "strategy_instance_id": "x",
        }
    )
    known = ledger.get_order_ids("BTC/USDT-P")
    assert "known-1" in known
    assert "unknown-2" not in known
    ledger.close()
