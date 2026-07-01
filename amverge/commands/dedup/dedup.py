from __future__ import annotations

from pathlib import Path

import typer

from ...ui import banner, console, err, make_progress, ok, fail
from ...core.dedup import DEDUP_METHODS


def dedup(
    input: Path = typer.Argument(..., help="Input video file"),
    output: Path = typer.Option(None, "--output", "-o", help="Output video file"),
    method: str = typer.Option("ffmpeg", "--method", "-m", help="Dedup method: ffmpeg, ssim, framediff"),
    threshold: float = typer.Option(2.0, "--threshold", "-t", help="Detection threshold (method-specific)"),
    min_change_pct: float = typer.Option(2.0, "--min-change-pct", help="Min changed pixel %% for framediff method"),
    list_methods: bool = typer.Option(False, "--list-methods", help="List available dedup methods"),
) -> None:
    """Remove duplicate / dead frames from a video.

    Supports three methods: ffmpeg (mpdecimate, no deps), ssim (OpenCV, quality-aware),
    and framediff (OpenCV, pixel motion detection).
    """
    if list_methods:
        banner("dedup methods")
        console.print()
        for key, entry in DEDUP_METHODS.items():
            req = entry.get("requires") or "none"
            console.print(f"  [accent]{key}[/accent] - {entry['name']}")
            console.print(f"    {entry['description']}")
            console.print(f"    Requires: [dim]{req}[/]")
        console.print()
        return

    if not input.exists():
        fail(f"File not found: {input}")
        raise typer.Exit(1)

    if method not in DEDUP_METHODS:
        fail(f"Unknown method '{method}'. Valid: {', '.join(DEDUP_METHODS.keys())}")
        raise typer.Exit(1)

    if output is None:
        stem = input.stem
        output = input.parent / f"{stem}_deduped{input.suffix}"

    entry = DEDUP_METHODS[method]

    banner("dedup")

    console.print(f"  Method: [accent]{entry['name']}[/accent]")
    console.print(f"  Threshold: [accent]{threshold}[/accent]")
    if method == "framediff":
        console.print(f"  Min change: [accent]{min_change_pct}%[/accent]")
    console.print(f"  Input:  [dim]{input}[/dim]")
    console.print(f"  Output: [dim]{output}[/dim]")

    with make_progress() as progress:
        task_id = progress.add_task("Dedup...", total=100)

        def _progress_cb(pct, msg):
            progress.update(task_id, completed=pct, description=msg)

        try:
            if method == "ffmpeg":
                from ...core.dedup import dedup_ffmpeg
                dedup_ffmpeg(str(input.resolve()), str(output.resolve()), threshold, _progress_cb)
            elif method == "ssim":
                from ...core.dedup import dedup_ssim, SSIM_AVAILABLE
                if not SSIM_AVAILABLE:
                    fail("SSIM method requires opencv and scikit-image. Run: pip install opencv-python scikit-image")
                    raise typer.Exit(1)
                dedup_ssim(str(input.resolve()), str(output.resolve()), threshold, _progress_cb)
            elif method == "framediff":
                from ...core.dedup import dedup_framediff, FRAMEDIFF_AVAILABLE
                if not FRAMEDIFF_AVAILABLE:
                    fail("FrameDiff method requires opencv. Run: pip install opencv-python")
                    raise typer.Exit(1)
                dedup_framediff(str(input.resolve()), str(output.resolve()), threshold, min_change_pct, _progress_cb)
        except Exception as e:
            fail(str(e))
            raise typer.Exit(1)

    ok(f"Saved: {output}")
