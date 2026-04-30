import json, os
from datetime import datetime, timezone

class AuditLogger:
    def __init__(self, path:str):
        self.path=path
        os.makedirs(os.path.dirname(path), exist_ok=True)
    def log(self, event:str, **data):
        row={"ts":datetime.now(timezone.utc).isoformat(),"event":event,**data}
        with open(self.path,"a",encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False)+"\n")
