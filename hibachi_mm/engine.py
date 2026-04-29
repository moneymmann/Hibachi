from .models import MarketSnapshot

class Engine:
    def __init__(self, mode: str = "dry-run"):
        self.mode = mode
        self.started = False
    def heartbeat(self):
        return {"ok": True, "mode": self.mode}
    def dry_run_place_order(self, *_args, **_kwargs):
        return {"submitted": self.mode == "live"}
    def snapshot(self):
        return MarketSnapshot(100.0, 101.0, 100.5, 1, 99.5)
