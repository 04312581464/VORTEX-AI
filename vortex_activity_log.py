from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ActivityEvent:
    ts: str
    kind: str
    message: str
    meta: Dict[str, Any]


class ActivityLogger:
    """
    Append-only JSONL activity log for transparency.
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, kind: str, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
        evt = ActivityEvent(ts=_utc_now_iso(), kind=kind, message=message, meta=meta or {})
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evt.__dict__, ensure_ascii=False) + "\n")

    def iter_events(self) -> Iterable[ActivityEvent]:
        if not self.log_path.exists():
            return []
        events: List[ActivityEvent] = []
        with self.log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    events.append(
                        ActivityEvent(
                            ts=str(obj.get("ts", "")),
                            kind=str(obj.get("kind", "")),
                            message=str(obj.get("message", "")),
                            meta=dict(obj.get("meta") or {}),
                        )
                    )
                except Exception:
                    continue
        return events

    def get_today(self, local_tz: Optional[timezone] = None) -> List[ActivityEvent]:
        tz = local_tz or datetime.now().astimezone().tzinfo or timezone.utc
        today = datetime.now(tz).date()
        out: List[ActivityEvent] = []
        for e in self.iter_events():
            try:
                dt = datetime.fromisoformat(e.ts.replace("Z", "+00:00")).astimezone(tz)
                if dt.date() == today:
                    out.append(e)
            except Exception:
                continue
        return out

