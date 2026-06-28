from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn

from ..core.binaries import get_ffmpeg

console = Console()
err = Console(stderr=True)

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

VALID_CODECS = {"copy", "h264", "hevc", "h265"}


def _parse_select(select: str, max_index: int) -> list[int]:
    indices: set[int] = set()
    for part in select.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            indices.update(range(int(lo), int(hi) + 1))
        else:
            indices.add(int(part))
    return sorted(i for i in indices if 0 <= i <= max_index)


def export(
    video: Path = typer.Argument(..., help="Original source video (used as -i for re-encode)", exists=True),
    scenes: Path = typer.Option(..., "--scenes", "-s", help="scenes.json from `detect`", exists=True),
    output: Path = typer.Option(Path("export"), "--output", "-o", help="Output directory"),
    select: Optional[str] = typer.Option(None, "--select", help='Scene indices: "0,2,5-8" (default: all)'),
    merge: bool = typer.Option(False, "--merge", help="Merge selected clips into one file"),
    codec: str = typer.Option("copy", "--codec", help="Video codec: copy, h264, hevc"),
) -> None:
    """Export selected scenes from a detect run."""
    if codec not in VALID_CODECS:
        err.print(f"[red]Unknown codec '{codec}'. Choose: {', '.join(sorted(VALID_CODECS))}")
        raise typer.Exit(1)
    if codec == "h265":
        codec = "hevc"

    payload = json.loads(scenes.read_text())
    all_scenes: list[dict] = payload.get("scenes", payload) if isinstance(payload, dict) else payload

    if not all_scenes:
        err.print("[red]No scenes in JSON.")
        raise typer.Exit(1)

    max_idx = max(s["scene_index"] for s in all_scenes)

    if select:
        selected_indices = _parse_select(select, max_idx)
        selected = [s for s in all_scenes if s["scene_index"] in selected_indices]
    else:
        selected = all_scenes

    if not selected:
        err.print("[red]No scenes matched selection.")
        raise typer.Exit(1)

    output.mkdir(parents=True, exist_ok=True)
    ff = get_ffmpeg()

    if merge:
        _export_merged(selected, output, ff, codec)
    else:
        _export_individual(selected, output, ff, codec)


def _ffmpeg_copy(src: str, dst: str, ff: str) -> None:
    subprocess.run(
        [ff, "-y", "-i", src, "-c", "copy", dst],
        capture_output=True, creationflags=CREATE_NO_WINDOW, check=True,
    )


def _export_individual(scenes: list[dict], output: Path, ff: str, codec: str) -> None:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=err,
    ) as progress:
        task = progress.add_task("Exporting...", total=len(scenes))

        for scene in scenes:
            src = scene["path"]
            idx = scene["scene_index"]
            dst = str(output / f"scene_{idx:04d}.mp4")

            if codec == "copy":
                _ffmpeg_copy(src, dst, ff)
            else:
                _encode(src, dst, ff, codec)

            progress.advance(task)
            progress.update(task, description=f"Exported scene {idx:04d}")

    console.print(f"[green]{len(scenes)} clips → {output}")


def _export_merged(scenes: list[dict], output: Path, ff: str, codec: str) -> None:
    err.print(f"Merging {len(scenes)} scenes...")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        concat_file = f.name
        for s in scenes:
            path = s["path"].replace("\\", "/")
            f.write(f"file '{path}'\n")

    dst = str(output / "merged.mp4")

    try:
        cmd = [ff, "-y", "-f", "concat", "-safe", "0", "-i", concat_file]
        if codec == "copy":
            cmd += ["-c", "copy"]
        else:
            cmd += ["-c:v", codec, "-c:a", "aac"]
        cmd.append(dst)

        subprocess.run(cmd, capture_output=True, creationflags=CREATE_NO_WINDOW, check=True)
    finally:
        os.unlink(concat_file)

    console.print(f"[green]Merged → {dst}")


def _encode(src: str, dst: str, ff: str, codec: str) -> None:
    subprocess.run(
        [ff, "-y", "-i", src, "-c:v", codec, "-c:a", "aac", "-b:a", "160k", dst],
        capture_output=True, creationflags=CREATE_NO_WINDOW, check=True,
    )
