from hibachi_mm.order_manager import enforce_one_per_side

def test_max_active_orders_per_side():
    out=enforce_one_per_side([{'side':'buy'},{'side':'buy'},{'side':'sell'}])
    assert len(out['buy'])==1 and len(out['sell'])==1
