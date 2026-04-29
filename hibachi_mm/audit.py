from pathlib import Path
import json, time

class AuditLogger:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: str, **payload):
        rec = {"ts": int(time.time()*1000), "event": event_type, **payload}
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
