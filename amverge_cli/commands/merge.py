from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

import typer
from rich.console import Console

from ..core.binaries import get_ffmpeg

console = Console()
err = Console(stderr=True)

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def merge(
    clips: List[Path] = typer.Argument(..., help="Clip files to merge in order"),
    output: Path = typer.Option(..., "--output", "-o", help="Output file path"),
) -> None:
    """Merge multiple clips into one file via FFmpeg concat."""
    for clip in clips:
        if not clip.exists():
            err.print(f"[red]Missing: {clip}")
            raise typer.Exit(1)

    ff = get_ffmpeg()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        concat_file = f.name
        for clip in clips:
            path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{path}'\n")

    try:
        err.print(f"Merging {len(clips)} clips → {output}")
        subprocess.run(
            [ff, "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", str(output)],
            capture_output=True,
            creationflags=CREATE_NO_WINDOW,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        err.print(f"[red]ffmpeg failed:\n{e.stderr.decode(errors='replace')[-1000:]}")
        raise typer.Exit(1)
    finally:
        os.unlink(concat_file)

    console.print(f"[green]Merged → {output}")
