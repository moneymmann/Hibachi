async def process_fills(engine, fills):
    for f in fills:
        side = getattr(f,'side',None) if not isinstance(f,dict) else f.get('side')
        price = getattr(f,'price',None) if not isinstance(f,dict) else f.get('price')
        qty = getattr(f,'quantity',None) if not isinstance(f,dict) else f.get('quantity')
        if side=='buy':
            await engine.exchange.place_reduce_only_take_profit('sell', engine.dec(price)+engine.market.tick_size, engine.dec(qty))
        elif side=='sell':
            await engine.exchange.place_reduce_only_take_profit('buy', engine.dec(price)-engine.market.tick_size, engine.dec(qty))
