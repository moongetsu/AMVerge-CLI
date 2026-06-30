from __future__ import annotations

import os
from pathlib import Path

import typer

from ...ui import banner, console, make_progress, ok, fail, dim
from ...core.infra.diagnostics import get_gpu_info
from ...core.infra.ffmpeg_bootstrap import is_portable_ffmpeg_installed, ensure_ffmpeg
from ...core.upscaling.registry import (
    UPSCALE_REGISTRY,
    QUALITY_PRESETS,
    get_ml_models,
    get_shader_models,
    get_onnx_models,
    get_model_scales,
    get_model_credit,
)


def _ensure_ffmpeg_interactive(auto_yes=False):
    if not is_portable_ffmpeg_installed():
        console.print("  [warn]FFmpeg not found on your system.[/warn]")
        if auto_yes or typer.confirm("  Download portable FFmpeg?", default=True):
            with make_progress() as progress:
                task_id = progress.add_task("Downloading FFmpeg...", total=100)
                def _cb(pct, msg):
                    progress.update(task_id, completed=pct, description=msg)
                try:
                    ensure_ffmpeg(progress_cb=_cb)
                    ok("FFmpeg installed")
                except Exception as e:
                    fail(str(e))
                    raise typer.Exit(1)
        else:
            fail("FFmpeg is required: https://ffmpeg.org/download.html")
            raise typer.Exit(1)


def _ensure_model_downloaded(model_key, auto_yes=False):
    from ...core.upscaling.weight_loader import is_weight_downloaded, download_weights
    if is_weight_downloaded(model_key):
        return
    entry = UPSCALE_REGISTRY.get(model_key, {})
    name = entry.get("name", model_key)
    console.print(f"  [warn]Model '{name}' not downloaded.[/warn]")
    if auto_yes or typer.confirm(f"  Download {name}?", default=True):
        with make_progress() as progress:
            task_id = progress.add_task(f"Downloading {name}...", total=100)
            def _cb(pct, msg):
                progress.update(task_id, completed=pct, description=msg)
            if not download_weights(model_key, progress_cb=_cb):
                fail(f"Download failed for {name}")
                raise typer.Exit(1)
            ok(f"Model {name} downloaded")
    else:
        fail(f"Model {name} is required")
        raise typer.Exit(1)


def upscale(
    model: str = typer.Option("adore", "--model", "-m", help="Model key from registry (see --list-models)"),
    input: Path = typer.Argument(None, help="Input video file"),
    output: Path = typer.Option(Path("upscaled.mp4"), "--output", "-o", help="Output video file"),
    scale: int = typer.Option(2, "--scale", "-s", help="Scale factor (model-specific)"),
    preset: str = typer.Option("high", "--preset", "-p", help="Quality: archival, high, balanced, fast, draft"),
    mode: str = typer.Option("medium", "--mode", help="Shader mode: light, medium, strong"),
    fit_w: int = typer.Option(0, "--fit-w", help="Max output width (0 = no limit)"),
    fit_h: int = typer.Option(0, "--fit-h", help="Max output height (0 = no limit)"),
    list_models: bool = typer.Option(False, "--list-models", help="List all available models"),
    credits: bool = typer.Option(False, "--credits", help="Show credits for upscaling technologies"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-confirm all download prompts"),
) -> None:
    """Upscale video using AI super-resolution.

    All models and methods are defined in registry.json. Use --list-models to browse.
    """
    if list_models:
        banner("upscale models")
        console.print()
        for key, entry in UPSCALE_REGISTRY.items():
            scales_str = "/".join(f"{s}x" for s in entry["scales"])
            console.print(f"  [accent]{key}[/accent]  {entry['name']}  dim:{entry['method']}  {scales_str}")
            console.print(f"    {entry.get('description', '')}")
            console.print(f"    Credit: {entry.get('credit', '')}")
        console.print()
        return

    if credits:
        banner("upscale credits")
        console.print()
        seen = set()
        for entry in UPSCALE_REGISTRY.values():
            cred = entry.get("credit", "")
            if cred and cred not in seen:
                console.print(f"  [accent]+[/accent] {cred}")
                seen.add(cred)
        console.print()
        return

    if input is None:
        fail("Missing INPUT argument.")
        raise typer.Exit(1)
    if not input.exists():
        fail(f"File not found: {input}")
        raise typer.Exit(1)

    if model not in UPSCALE_REGISTRY:
        fail(f"Unknown model '{model}'. Use --list-models to see available models.")
        raise typer.Exit(1)

    entry = UPSCALE_REGISTRY[model]
    method = entry["method"]

    valid_scales = get_model_scales(model)
    if scale not in valid_scales:
        scales_str = "/".join(f"{s}x" for s in valid_scales)
        fail(f"Model '{model}' supports {scales_str}, got {scale}x")
        raise typer.Exit(1)

    if preset not in QUALITY_PRESETS:
        fail(f"Unknown preset '{preset}'. Valid: {', '.join(QUALITY_PRESETS.keys())}")
        raise typer.Exit(1)

    banner("upscale")

    if method in ("ml", "onnx"):
        try:
            from ...core.upscaling.engine import UPSCALE_AVAILABLE
        except ImportError:
            fail("Upscaling module not available. Dependencies missing.")
            raise typer.Exit(1)

        if method == "ml" and not UPSCALE_AVAILABLE:
            fail("ML upscaling requires torch and opencv. Run: pip install amverge[upscale]")
            raise typer.Exit(1)

        _ensure_ffmpeg_interactive(auto_yes=yes)
        _ensure_model_downloaded(model, auto_yes=yes)

        if method == "ml":
            gpu_info = get_gpu_info()
            if gpu_info.get("cuda_available"):
                vram = gpu_info.get("vram_gb", 0)
                console.print(f"  GPU: [accent]{gpu_info.get('gpu_name', 'N/A')}[/accent]  "
                              f"VRAM: [accent]{vram:.1f} GB[/accent]")
            else:
                console.print("  [warn]No NVIDIA GPU detected. Upscaling on CPU will be very slow.[/warn]")

        console.print(f"  Model: [accent]{entry.get('name', model)}[/accent]  "
                      f"Scale: [accent]{scale}x[/accent]  "
                      f"Preset: [accent]{preset}[/accent]")
        console.print(f"  Input: [dim]{input}[/dim]")
        console.print(f"  Output: [dim]{output}[/dim]")

    elif method == "shader":
        _ensure_ffmpeg_interactive(auto_yes=yes)

        shader_modes = entry.get("modes", ["medium"])
        if mode not in shader_modes:
            fail(f"Unknown mode '{mode}'. Valid: {', '.join(shader_modes)}")
            raise typer.Exit(1)

        console.print(f"  Method: [accent]{entry.get('name', model)}[/accent] (FFmpeg filters, no ML)")
        console.print(f"  Mode: [accent]{mode}[/accent]  "
                      f"Scale: [accent]{scale}x[/accent]  "
                      f"Preset: [accent]{preset}[/accent]")
        console.print(f"  Input: [dim]{input}[/dim]")
        console.print(f"  Output: [dim]{output}[/dim]")

    from ...core.upscaling.engine import upscale_model

    with make_progress() as progress:
        task_id = progress.add_task("Upscaling...", total=100)
        def _progress_cb(pct, msg):
            progress.update(task_id, completed=pct, description=msg)

        try:
            upscale_model(
                model_key=model,
                input_path=str(input.resolve()),
                output_path=str(output.resolve()),
                scale=scale,
                preset=preset,
                fit_w=fit_w,
                fit_h=fit_h,
                mode=mode if method == "shader" else None,
                progress_cb=_progress_cb,
            )
        except Exception as e:
            fail(str(e))
            raise typer.Exit(1)

    ok(f"Upscaled video saved to {output}")
