from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
import json

try:
    import orjson  # type: ignore
except Exception:
    orjson = None


class AuditLogger:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, payload: dict | object) -> None:
        body = asdict(payload) if is_dataclass(payload) else dict(payload)
        row = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **body}
        with self.path.open("ab") as f:
            if orjson is not None:
                f.write(orjson.dumps(row))
            else:
                f.write(json.dumps(row, ensure_ascii=False).encode("utf-8"))
            f.write(b"\n")
