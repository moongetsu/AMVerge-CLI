from __future__ import annotations

import sys
import threading

_lock = threading.Lock()


def emit_progress(percent: int, message: str) -> None:
    clamped = max(0, min(100, int(percent)))
    with _lock:
        print(f"PROGRESS|{clamped}|{message}", file=sys.stderr, flush=True)


def emit_event(event_type: str, payload: str = "") -> None:
    with _lock:
        if payload:
            print(f"{event_type}|{payload}", file=sys.stderr, flush=True)
        else:
            print(event_type, file=sys.stderr, flush=True)
