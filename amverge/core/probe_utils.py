from __future__ import annotations

import subprocess
from pathlib import Path

from .binaries import get_ffprobe


def probe_video_fps(input_video: str | Path) -> float:
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
    return int(video_fps * video_duration)
