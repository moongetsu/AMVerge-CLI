from __future__ import annotations

"""ffprobe wrappers for video metadata.

Convenience functions that shell out to ffprobe for common probe queries.
All functions accept a ``str`` or ``Path`` and return typed values.

Example:
    >>> from amverge.core.probe_utils import probe_video_fps, probe_video_dimensions
    >>> fps = probe_video_fps("episode.mp4")
    >>> w, h = probe_video_dimensions("episode.mp4")
"""

import subprocess
from pathlib import Path

from .binaries import get_ffprobe


def probe_video_fps(input_video: str | Path) -> float:
    """Get the frame rate of the first video stream.

    Returns:
        FPS as a float (e.g. 23.976, 24.0, 30.0).
    """
    cmd = [
        get_ffprobe(),
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(input_video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    num, den = map(int, result.stdout.strip().split("/"))
    return num / den


def probe_video_dimensions(input_video: str | Path) -> tuple[int, int]:
    """Get the width and height of the first video stream.

    Returns:
        ``(width, height)`` tuple in pixels.
    """
    cmd = [
        get_ffprobe(),
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        str(input_video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    width, height = map(int, result.stdout.strip().split("x"))
    return width, height


def probe_video_duration(input_video: str | Path) -> float:
    """Get the total duration of the video.

    Returns:
        Duration in seconds as a float.
    """
    cmd = [
        get_ffprobe(),
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(input_video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def probe_video_total_frames(input_video: str | Path, video_fps: float, video_duration: float) -> int:
    """Estimate total frame count from FPS and duration.

    Args:
        video_fps: Frame rate from :func:`probe_video_fps`.
        video_duration: Duration from :func:`probe_video_duration`.

    Returns:
        Estimated frame count as ``int(fps * duration)``.
    """
    return int(video_fps * video_duration)
