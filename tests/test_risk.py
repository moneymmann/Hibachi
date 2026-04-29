from hibachi_mm.risk import allow_entry

def test_risk_blocks_low_margin():
    ok,reason=allow_entry(10,35)
    assert not ok and reason=='low_free_margin'
