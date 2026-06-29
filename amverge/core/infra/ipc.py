from __future__ import annotations

"""IPC protocol for the AMVerge Tauri backend.

Emits structured events to stderr for the Rust frontend to consume.
stdout is reserved for final JSON output. Never mix IPC output with
Rich/progress output in the same process.

Events:
    ``PROGRESS|pct|msg``  progress update (0-100)
    ``INITIAL_CLIPS_READY|json``  initial scene list from TransNetV2
    ``CLIP_READY|idx|path|mode``  single scene cut complete
    ``PHASE1_COMPLETE``  all lossless copy scenes done
    ``REENCODE_PROGRESS|done|total``  re-encode phase progress
"""

import hashlib
import os
import sys
import threading
from pathlib import Path

_lock = threading.Lock()


def emit_progress(percent: int, message: str) -> None:
    """Emit a progress update event to stderr.

    Format: ``PROGRESS|<clamped_pct>|<message>``

    Args:
        percent: 0-100 progress value (clamped).
        message: Human-readable status message.
    """
    clamped = max(0, min(100, int(percent)))
    with _lock:
        print(f"PROGRESS|{clamped}|{message}", file=sys.stderr, flush=True)


def emit_event(line: str) -> None:
    """Emit a raw IPC event line to stderr.

    Args:
        line: Full event string (e.g. ``"CLIP_READY|0|path|copy"``).
    """
    with _lock:
        print(line, file=sys.stderr, flush=True)


def log(message: str) -> None:
    """Write a log message to stderr. Silently ignores errors.

    Args:
        message: Arbitrary string to log.
    """
    try:
        print(str(message), file=sys.stderr, flush=True)
    except Exception:
        pass


def check_if_path_exists(path_str: str) -> bool:
    """Verify a path exists, raising ``FileNotFoundError`` if not.

    Args:
        path_str: File or directory path to check.

    Returns:
        True if the path exists.

    Raises:
        FileNotFoundError: If the path does not exist.
    """
    if not os.path.exists(path_str):
        raise FileNotFoundError(f"Path does not exist: {path_str}")
    return True


def build_video_cache_prefix(input_video: Path) -> str:
    """Generate a unique cache prefix from a video file's fingerprint.

    Uses file path, size, and mtime to produce a SHA1-based prefix that
    identifies a specific video file across sessions.

    Args:
        input_video: Path to the video file.

    Returns:
        String like ``"scenes_be84f8c8a759"`` - a 12-hex-char digest
        prefixed with ``scenes_``.
    """
    stat = input_video.stat()
    fingerprint = f"{input_video.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"
    digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:12]
    return f"scenes_{digest}"
