from __future__ import annotations

import os
from pathlib import Path

import typer

from ...ui import banner, console, make_progress, ok, fail
from ...core.interpolation import (
    flowframes_available,
    run_flowframes,
    get_flowframes_path,
    set_flowframes_path,
)


def flowframes(
    input: Path = typer.Argument(..., help="Input video file"),
    output: Path = typer.Option(Path("interpolated.mp4"), "--output", "-o", help="Output video file"),
    factor: int = typer.Option(2, "--factor", "-f", help="Frame rate multiplier (2x-16x)"),
    ai: str = typer.Option("RifeNcnn", "--ai", help="AI implementation for Flowframes 1.42.0"),
    model: str = typer.Option("RIFE 4.26", "--model", "-m", help="Interpolation model name"),
    output_format: str = typer.Option("Mp4", "--format", help="Output format"),
    encoder: str = typer.Option("X264", "--encoder", "-e", help="Video encoder"),
    pix_fmt: str = typer.Option("Yuv420P", "--pix-fmt", help="Pixel format"),
    quality: float = typer.Option(None, "--quality", "-q", help="Quality setting (integer, higher = better)"),
    max_fps: float = typer.Option(None, "--max-fps", help="Max output FPS cap"),
    max_height: int = typer.Option(None, "--max-height", help="Max output height"),
    scene_change: bool = typer.Option(False, "--scene-change", help="Enable scene change detection"),
    scene_sensitivity: float = typer.Option(None, "--scene-sensitivity", help="Scene change sensitivity"),
    ff_path: Path = typer.Option(None, "--ff-path", help="Path to Flowframes.exe"),
    timeout: float = typer.Option(36000.0, "--timeout", help="Max runtime in seconds (default 10 hours)"),
) -> None:
    """Run Flowframes 1.42.0 frame interpolation.

    Requires Flowframes 1.42.0 Patreon installed. Auto-detects at %LOCALAPPDATA%\\Flowframes\\Flowframes.exe
    or configure with: amverge flowframes-path PATH
    """
    if ff_path:
        if not ff_path.exists():
            fail(f"Flowframes.exe not found: {ff_path}")
            raise typer.Exit(1)
        set_flowframes_path(str(ff_path))
        ok(f"Flowframes path saved: {ff_path}")

    if not input.exists():
        fail(f"File not found: {input}")
        raise typer.Exit(1)

    if not flowframes_available():
        fail(
            "Flowframes.exe (1.42.0) not found.\n"
            "  Set path:  amverge flowframes-path PATH"
        )
        raise typer.Exit(1)

    if factor < 2 or factor > 16:
        fail("Factor must be between 2 and 16")
        raise typer.Exit(1)

    banner("flowframes")

    ff_exe = get_flowframes_path()
    console.print(f"  Flowframes: [accent]{ff_exe}[/accent]")
    console.print(f"  AI: [accent]{ai}[/accent]  Model: [accent]{model}[/accent]  Factor: [accent]{factor}x[/accent]")
    console.print(f"  Input:  [dim]{input}[/dim]")
    console.print(f"  Output: [dim]{output}[/dim]")

    output_dir = str(output.parent.resolve()) if output.parent != Path(".") else os.path.join(os.getcwd(), ".")
    output_basename = output.name

    with make_progress() as progress:
        task_id = progress.add_task("Interpolating...", total=100)

        def _progress_cb(pct: int, msg: str) -> None:
            progress.update(task_id, completed=pct, description=msg)

        try:
            produced = run_flowframes(
                input_path=str(input.resolve()),
                output_dir=output_dir,
                factor=factor,
                ai=ai,
                model=model,
                output_format=output_format,
                encoder=encoder,
                pix_fmt=pix_fmt,
                quality=int(quality) if quality is not None else None,
                max_fps=max_fps,
                max_height=max_height,
                scene_change=scene_change,
                scene_sensitivity=scene_sensitivity,
                progress_cb=_progress_cb,
                timeout=timeout,
            )
        except Exception as e:
            fail(str(e))
            raise typer.Exit(1)

    produced_path = Path(produced)
    expected_path = Path(output_dir) / output_basename

    if produced_path != expected_path:
        try:
            produced_path.rename(expected_path)
            ok(f"Renamed output: {expected_path}")
        except OSError:
            ok(f"Saved: {produced_path}")
    else:
        ok(f"Saved: {expected_path}")
