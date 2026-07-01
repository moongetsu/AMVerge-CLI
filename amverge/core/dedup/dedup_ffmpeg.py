from __future__ import annotations

import os
import subprocess
import sys
from typing import Callable, Optional

from ..infra.binaries import get_ffmpeg, get_ffprobe

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def dedup_ffmpeg(
    video_path: str,
    output_path: str,
    threshold: float = 2.0,
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> str:
    """Remove duplicate frames using FFmpeg mpdecimate filter.

    Args:
        video_path: Path to input video.
        output_path: Path for output video.
        threshold: Maximum number of duplicate frames to drop per batch (hi param).
        progress_cb: Optional (pct, msg) callback.

    Returns:
        Output path on success.
    """
    ffmpeg = get_ffmpeg()

    if progress_cb:
        progress_cb(0, "Removing duplicate frames (mpdecimate)...")

    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_path,
        "-vf", f"mpdecimate=hi={int(threshold)}",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                           creationflags=CREATE_NO_WINDOW)
        if r.returncode != 0:
            raise RuntimeError(f"FFmpeg mpdecimate failed: {r.stderr.strip()}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg mpdecimate timed out after 1 hour")

    if progress_cb:
        progress_cb(100, "Complete")

    return output_path
