from __future__ import annotations

import os
import sys
from pathlib import Path
from shutil import which

if getattr(sys, "frozen", False):
    _ROOT = Path(sys.executable).resolve().parent
else:
    _ROOT = Path(__file__).resolve().parent.parent


def _platform_names(name: str) -> list[str]:
    if os.name == "nt" and not name.lower().endswith(".exe"):
        return [f"{name}.exe", name]
    return [name]


def get_binary(name: str) -> str:
    search_dirs = [
        _ROOT / "_internal",
        _ROOT,
        _ROOT / "bin",
    ]

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        search_dirs.extend([
            exe_dir / "_internal",
            exe_dir,
            exe_dir / "bin",
        ])

    names = _platform_names(name)

    for directory in search_dirs:
        for candidate_name in names:
            candidate = directory / candidate_name
            if candidate.exists():
                return str(candidate)

    for candidate_name in names:
        found = which(candidate_name)
        if found:
            found_path = Path(found)
            if found_path.is_absolute() and found_path.exists():
                return str(found_path)

    return str(search_dirs[0] / names[0])


def get_ffmpeg() -> str:
    return get_binary("ffmpeg")


def get_ffprobe() -> str:
    return get_binary("ffprobe")
