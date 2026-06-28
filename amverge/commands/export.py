from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import typer

from ..core.binaries import get_ffmpeg
from ..core.discord_rpc import RPC_AVAILABLE, DiscordRPC
from ..ui import banner, console, err, make_progress, make_table, ok, fail, dim

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
VALID_CODECS = {"copy", "h264", "hevc", "h265"}
VALID_AUDIO = {"copy", "aac", "aac_320", "pcm16", "pcm24", "flac", "alac", "opus", "mp3", "none"}
VALID_CONTAINERS = {"mp4", "mkv", "mov"}

AUDIO_FFMPEG: dict[str, list[str]] = {
    "copy":     ["-c:a", "copy"],
    "aac":      ["-c:a", "aac"],
    "aac_320":  ["-c:a", "aac", "-b:a", "320k"],
    "pcm16":    ["-c:a", "pcm_s16le"],
    "pcm24":    ["-c:a", "pcm_s24le"],
    "flac":     ["-c:a", "flac"],
    "alac":     ["-c:a", "alac"],
    "opus":     ["-c:a", "libopus"],
    "mp3":      ["-c:a", "libmp3lame"],
    "none":     ["-an"],
}


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
    video: Path = typer.Argument(..., help="Source video file", exists=True),
    scenes: Path = typer.Option(..., "--scenes", "-s", help="scenes.json from detect", exists=True),
    output: Path = typer.Option(Path("export"), "--output", "-o", help="Output directory"),
    select: Optional[str] = typer.Option(None, "--select", help='Indices: "0,2,5-8" (default: all)'),
    merge: bool = typer.Option(False, "--merge", help="Merge selected clips into one file"),
    codec: str = typer.Option("copy", "--codec", help="copy · h264 · hevc"),
    audio: str = typer.Option("copy", "--audio", help="copy · aac · aac_320 · pcm16 · pcm24 · flac · alac · opus · mp3 · none"),
    container: str = typer.Option("mp4", "--container", help="mp4 · mkv · mov"),
    no_rpc: bool = typer.Option(False, "--no-rpc", help="Disable Discord RPC"),
) -> None:
    """Export selected scenes from a detect run."""
    if codec not in VALID_CODECS:
        fail(f"Unknown codec '{codec}'. Valid: {', '.join(sorted(VALID_CODECS))}")
        raise typer.Exit(1)
    if audio not in VALID_AUDIO:
        fail(f"Unknown audio '{audio}'. Valid: {', '.join(sorted(VALID_AUDIO))}")
        raise typer.Exit(1)
    if container not in VALID_CONTAINERS:
        fail(f"Unknown container '{container}'. Valid: {', '.join(sorted(VALID_CONTAINERS))}")
        raise typer.Exit(1)
    if codec == "h265":
        codec = "hevc"

    banner("export")

    rpc = DiscordRPC() if RPC_AVAILABLE and not no_rpc else None
    if rpc:
        rpc.connect()
        rpc.update_exporting(video.name)

    payload = json.loads(scenes.read_text())
    all_scenes: list[dict] = payload.get("scenes", payload) if isinstance(payload, dict) else payload

    if not all_scenes:
        fail("No scenes in JSON.")
        raise typer.Exit(1)

    max_idx = max(s["scene_index"] for s in all_scenes)
    selected = (
        [s for s in all_scenes if s["scene_index"] in _parse_select(select, max_idx)]
        if select else all_scenes
    )

    if not selected:
        fail("No scenes matched selection.")
        raise typer.Exit(1)

    output.mkdir(parents=True, exist_ok=True)
    ff = get_ffmpeg()

    try:
        if merge:
            _export_merged(selected, output, ff, codec, audio, container)
        else:
            _export_individual(selected, output, ff, codec, audio, container)
        if rpc:
            rpc.update_complete()
    except Exception:
        if rpc:
            rpc.update_error("Export failed")
        raise
    finally:
        if rpc:
            rpc.clear_presence()
            rpc.disconnect()


def _copy(src: str, dst: str, ff: str, audio: str) -> None:
    cmd = [ff, "-y", "-i", src]
    if audio == "copy":
        cmd += ["-c", "copy"]
    else:
        cmd += ["-c:v", "copy"]
        cmd += AUDIO_FFMPEG[audio]
    cmd.append(dst)
    subprocess.run(cmd, capture_output=True, creationflags=CREATE_NO_WINDOW, check=True)


def _encode(src: str, dst: str, ff: str, codec: str, audio: str) -> None:
    cmd = [ff, "-y", "-i", src, "-c:v", codec]
    cmd += AUDIO_FFMPEG[audio]
    cmd.append(dst)
    subprocess.run(cmd, capture_output=True, creationflags=CREATE_NO_WINDOW, check=True)


def _export_individual(scenes: list[dict], output: Path, ff: str, codec: str, audio: str, container: str) -> None:
    with make_progress(show_count=True) as progress:
        task = progress.add_task(f"Exporting {len(scenes)} clips", total=len(scenes))
        for s in scenes:
            idx = s["scene_index"]
            dst = str(output / f"scene_{idx:04d}.{container}")
            if codec == "copy":
                _copy(s["path"], dst, ff, audio)
            else:
                _encode(s["path"], dst, ff, codec, audio)
            progress.advance(task)
            progress.update(task, description=f"Exported scene_{idx:04d}")

    ok(f"{len(scenes)} clips → {output}")


def _export_merged(scenes: list[dict], output: Path, ff: str, codec: str, audio: str, container: str) -> None:
    with make_progress() as progress:
        task = progress.add_task(f"Merging {len(scenes)} clips", total=1)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            concat_file = f.name
            for s in scenes:
                f.write(f"file '{s['path'].replace(chr(92), '/')}'\n")

        dst = str(output / f"merged.{container}")
        try:
            cmd = [ff, "-y", "-f", "concat", "-safe", "0", "-i", concat_file]
            if codec == "copy":
                if audio == "copy":
                    cmd += ["-c", "copy"]
                else:
                    cmd += ["-c:v", "copy"]
                    cmd += AUDIO_FFMPEG[audio]
            else:
                cmd += ["-c:v", codec]
                cmd += AUDIO_FFMPEG[audio]
            cmd.append(dst)
            subprocess.run(cmd, capture_output=True, creationflags=CREATE_NO_WINDOW, check=True)
        finally:
            os.unlink(concat_file)

        progress.update(task, completed=1)

    ok(f"Merged → {dst}")
