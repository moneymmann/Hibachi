from hibachi_mm.fill_manager import take_profit_from_fill

def test_buy_fill_creates_sell_reduce_only_take_profit():
    o=take_profit_from_fill('buy',100,1,1)
    assert o['side']=='sell' and o['reduce_only']

def test_sell_fill_creates_buy_reduce_only_take_profit():
    o=take_profit_from_fill('sell',100,1,1)
    assert o['side']=='buy' and o['reduce_only']
