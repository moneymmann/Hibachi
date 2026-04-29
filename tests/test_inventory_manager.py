from hibachi_mm.inventory_manager import skew_sizes

def test_position_skew_long_short():
    b,a=skew_sizes(1,10)
    assert b<a
    b2,a2=skew_sizes(1,-10)
    assert b2>a2
