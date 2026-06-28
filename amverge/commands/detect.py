from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer

from ..pipeline import detect_scenes, DetectResult
from ..ui import banner, console, err, make_progress, make_table, ok, fail, dim
from ..core.discord_rpc import RPC_AVAILABLE, DiscordRPC

_STAGE_LABELS = {
    "detect":     "Detecting cuts",
    "segment":    "Cutting scenes",
    "thumbnails": "Thumbnails",
    "similarity": "Similarity check",
}


def detect(
    video: Path = typer.Argument(..., help="Input video file", exists=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    method: str = typer.Option("keyframe", "--method", "-m", help="keyframe · edge"),
    format: str = typer.Option("table", "--format", "-f", help="table · json · paths"),
    json_output: Optional[Path] = typer.Option(None, "--json-output", help="Save JSON to file"),
    no_thumbnails: bool = typer.Option(False, "--no-thumbnails"),
    no_similarity: bool = typer.Option(False, "--no-similarity"),
    min_duration: float = typer.Option(0.25, "--min-duration"),
    workers: int = typer.Option(4, "--workers"),
    similarity_threshold: float = typer.Option(0.10, "--similarity-threshold"),
    edge_threshold: float = typer.Option(0.15, "--edge-threshold"),
    edge_radius: float = typer.Option(0.6, "--edge-radius"),
    ipc: bool = typer.Option(False, "--ipc", hidden=True, help="Emit IPC events for Tauri app"),
    no_rpc: bool = typer.Option(False, "--no-rpc", help="Disable Discord RPC"),
) -> None:
    """Detect scenes in a video file."""
    fmt = format.lower()
    if fmt not in ("table", "json", "paths"):
        fail("--format must be: table, json, or paths")
        raise typer.Exit(1)
    if method not in ("keyframe", "edge"):
        fail("--method must be: keyframe or edge")
        raise typer.Exit(1)

    if ipc:
        _detect_ipc(video, output, method, min_duration, workers, similarity_threshold, edge_threshold, edge_radius)
        return

    banner("detect")

    rpc = DiscordRPC() if RPC_AVAILABLE and not no_rpc else None
    if rpc:
        rpc.connect()
        rpc.update_detecting(video.name)

    try:
        with make_progress() as progress:
            tasks: dict[str, object] = {}

            def on_progress(stage: str, pct: int, msg: str) -> None:
                label = _STAGE_LABELS.get(stage, stage)
                if stage not in tasks:
                    tasks[stage] = progress.add_task(label, total=100)
                progress.update(tasks[stage], completed=pct, description=label)
                if rpc and stage == "detect":
                    rpc.update_detecting(video.name, pct)

            result: DetectResult = detect_scenes(
                str(video.resolve()),
                output_dir=str(output.resolve()) if output else None,
                method=method,
                min_duration=min_duration,
                thumbnails=not no_thumbnails,
                similarity=not no_similarity and not no_thumbnails,
                similarity_threshold=similarity_threshold,
                thumbnail_workers=workers,
                edge_threshold=edge_threshold,
                edge_radius=edge_radius,
                progress=on_progress,
            )

        if rpc:
            rpc.update_complete()
    except Exception:
        if rpc:
            rpc.update_error("Detection failed")
        raise
    finally:
        if rpc:
            rpc.clear_presence()
            rpc.disconnect()

    if not result.scenes:
        fail("No scenes detected.")
        raise typer.Exit(1)

    if json_output:
        json_output.write_text(json.dumps(result.to_dict(), indent=2))
        ok(f"JSON saved to {json_output}")

    similar_set = {idx for pair in result.similar_pairs for idx in pair}

    if fmt == "json":
        console.print_json(json.dumps(result.to_dict()))
        return
    if fmt == "paths":
        for scene in result.scenes:
            console.print(scene.path)
        return

    t = make_table(
        ("#",        "muted",  {"justify": "right", "width": 5}),
        ("Start",    None,     {"justify": "right", "width": 9}),
        ("End",      None,     {"justify": "right", "width": 9}),
        ("Duration", None,     {"justify": "right", "width": 9}),
        ("~",        "warn",   {"justify": "center", "width": 3}),
        title=f"{video.stem}  ·  {len(result.scenes)} scenes  ·  {method}",
    )
    for s in result.scenes:
        t.add_row(
            str(s.index),
            f"{s.start:.2f}s",
            f"{s.end:.2f}s",
            f"{s.duration:.2f}s",
            "~" if s.index in similar_set else "",
        )
    console.print(t)
    dim(f"scenes.json saved to {result.scenes_json}")


def _detect_ipc(
    video: Path,
    output: Optional[Path],
    method: str,
    min_duration: float,
    workers: int,
    similarity_threshold: float,
    edge_threshold: float,
    edge_radius: float,
) -> None:
    import sys
    from ..core.ipc import emit_progress, emit_event
    from ..core.detection.keyframe import detect_cuts_by_keyframe
    from ..core.detection.edge import detect_cuts_by_edge
    from ..core.segmenter import run_ffmpeg_segment, collect_scenes
    from ..core.video import get_video_duration
    from ..core.thumbnails_streaming import generate_thumbnails_streaming

    video_path = str(video.resolve())
    video_stem = video.stem

    if output is None:
        output_dir = str(video.parent / f"{video_stem}_scenes")
    else:
        output_dir = str(output.resolve())

    os.makedirs(output_dir, exist_ok=True)

    emit_progress(10, "Extracting keyframes...")

    def kf_cb(pct: int, msg: str) -> None:
        emit_progress(pct, msg)

    if method == "keyframe":
        cut_points = detect_cuts_by_keyframe(video_path, min_duration=min_duration, progress_cb=kf_cb)
    else:
        cut_points = detect_cuts_by_edge(
            video_path,
            threshold=edge_threshold,
            radius=edge_radius,
            min_duration=min_duration,
            progress_cb=kf_cb,
        )

    emit_progress(50, f"Cutting {len(cut_points)} scenes...")

    seg_stem = video_stem.replace("%", "%%")
    output_pattern = os.path.join(output_dir, f"{seg_stem}_%04d.mp4")
    run_ffmpeg_segment(video_path, output_pattern, cut_points)

    total_duration = get_video_duration(video_path)
    scenes = collect_scenes(output_dir, video_stem, cut_points, total_duration)

    emit_progress(75, "Building scenes...")
    emit_progress(90, f"Generating thumbnails for {len(scenes)} scenes...")

    generate_thumbnails_streaming(output_dir, scenes, video_stem)

    emit_progress(100, "Done")
    print(json.dumps(scenes), flush=True)
