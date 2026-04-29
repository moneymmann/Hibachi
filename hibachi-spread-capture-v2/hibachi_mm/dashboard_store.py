import asyncio
class DashboardStore:
    def __init__(self): self.latest={}; self.log=[]; self._sockets=[]
    async def publish(self,payload):
        self.latest.update(payload); self.log.append(payload)
        for ws in list(self._sockets):
            try: await ws.send_json(payload)
            except Exception: self._sockets.remove(ws)
