from __future__ import annotations

import hashlib
import os
import sys
import threading
from pathlib import Path

_lock = threading.Lock()


def emit_progress(percent: int, message: str) -> None:
    clamped = max(0, min(100, int(percent)))
    with _lock:
        print(f"PROGRESS|{clamped}|{message}", file=sys.stderr, flush=True)


def emit_event(line: str) -> None:
    with _lock:
        print(line, file=sys.stderr, flush=True)


def log(message: str) -> None:
    try:
        print(str(message), file=sys.stderr, flush=True)
    except Exception:
        pass


def check_if_path_exists(path_str: str) -> bool:
    if not os.path.exists(path_str):
        raise FileNotFoundError(f"Path does not exist: {path_str}")
    return True


def build_video_cache_prefix(input_video: Path) -> str:
    stat = input_video.stat()
    fingerprint = f"{input_video.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"
    digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:12]
    return f"scenes_{digest}"
