from __future__ import annotations

import subprocess
from pathlib import Path

from .binaries import get_ffprobe


def check_if_hevc(video: str | Path) -> bool:
    path = str(video)
    if not path.strip():
        raise ValueError("No video path provided")

    cmd = [
        get_ffprobe(),
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name",
        "-of", "default=nk=1:nw=1",
        path,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        err = (p.stderr or "").strip()
        raise RuntimeError(
            f"ffprobe failed (exit {p.returncode})" + (f": {err}" if err else "")
        )
    return p.stdout.strip().lower() == "hevc"
