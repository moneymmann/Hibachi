from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path

import orjson


class AuditLogger:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, payload: dict | object) -> None:
        body = asdict(payload) if is_dataclass(payload) else dict(payload)
        row = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **body}
        with self.path.open("ab") as f:
            f.write(orjson.dumps(row))
            f.write(b"\n")
