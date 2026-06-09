# observability.py
"""Minimal JSONL observability: append one structured event per line.

Every record carries a UTC timestamp and an ``event`` name. Records from a
single ``loop`` run share a ``run_id`` so you can correlate LLM calls with the
iterations that produced them. The log path defaults to ``src/loop-logs.jsonl``
and can be overridden with the ``LOOP_LOG_PATH`` environment variable.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(
    os.environ.get("LOOP_LOG_PATH", Path(__file__).with_name("loop-logs.jsonl"))
)


def new_run_id() -> str:
    """A short, unique id used to group all records from one loop run."""
    return uuid.uuid4().hex[:12]


def log_event(event: str, **fields) -> None:
    """Append a single JSON record (one line) to the log file."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
