class OrderManager:
    def __init__(self, exchange, audit): self.exchange=exchange; self.audit=audit
    async def place_entry(self, side, price, qty):
        self.audit.log('place_order_intent', side=side, price=str(price), qty=str(qty))
        try:
            res=await self.exchange.place_entry_order(side,price,qty)
            self.audit.log('order_submitted', side=side)
            return res
        except Exception as e:
            self.audit.log('order_error', error=str(e)); raise
