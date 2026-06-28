from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import typer


def backend(
    video_path: str = typer.Argument(..., help="Input video file"),
    output_dir: str = typer.Argument(..., help="Output directory for scene clips"),
) -> None:
    """Drop-in replacement for the AMVerge Python backend sidecar.

    Called by Rust exactly like the original backend:
        amverge backend <video_path> <output_dir>

    Emits IPC events to stderr and final JSON to stdout.
    """
    from ..core.ipc import emit_progress, emit_event
    from ..core.detection.keyframe import detect_cuts_by_keyframe
    from ..core.segmenter import run_ffmpeg_segment, collect_scenes
    from ..core.video import get_video_duration
    from ..core.thumbnails_streaming import generate_thumbnails_streaming

    if not os.path.isfile(video_path):
        print(json.dumps([]), flush=True)
        print(f"Video not found: {video_path}", file=sys.stderr, flush=True)
        raise typer.Exit(1)

    os.makedirs(output_dir, exist_ok=True)

    video_stem = Path(video_path).stem

    emit_progress(10, "Extracting keyframes...")

    def kf_cb(pct: int, msg: str) -> None:
        emit_progress(pct, msg)

    cut_points = detect_cuts_by_keyframe(
        video_path,
        min_duration=0.25,
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
