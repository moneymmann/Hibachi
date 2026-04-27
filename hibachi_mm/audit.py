from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import orjson


class AuditLogger:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, payload: dict) -> None:
        enriched = {"ts": datetime.now(timezone.utc).isoformat(), **payload}
        with self.path.open("ab") as f:
            f.write(orjson.dumps(enriched))
            f.write(b"\n")
