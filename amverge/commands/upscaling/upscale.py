from __future__ import annotations

import os
from pathlib import Path

import typer

from ...ui import banner, console, make_progress, ok, fail, dim
from ...core.infra.diagnostics import get_gpu_info
from ...core.infra.ffmpeg_bootstrap import is_portable_ffmpeg_installed, ensure_ffmpeg


CREDITS_LINES = [
    "ShuffleCUGAN models based on AniSmooth by moongetsu",
    "Anime4K shaders by bloc97 (MIT License)",
    "ArtCNN models by Artoriuz",
]

UPSCALE_MODELS = ["adore", "shufflecugan", "fallin_soft", "fallin_strong"]
UPSCALE_METHODS = ["ml", "anime4k", "artcnn"]
UPSCALE_SCALES = [2, 4]
UPSCALE_PRESETS = ["archival", "high", "balanced", "fast", "draft"]
ANIME4K_MODES = ["light", "medium", "strong"]
ARTCNN_MODEL_NAMES = ["C4F16", "C4F32", "R8F64"]


def _ensure_ffmpeg(auto_yes=False):
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


def _ensure_anime4k_shaders(auto_yes=False):
    import glob
    from ...core.upscaling.anime4k import _get_anime4k_dir
    shader_dir = _get_anime4k_dir()
    glsl_files = glob.glob(os.path.join(shader_dir, "*.glsl")) if os.path.exists(shader_dir) else []
    if glsl_files:
        return
    console.print("  [warn]Anime4K shaders not downloaded.[/warn]")
    if auto_yes or typer.confirm("  Download Anime4K shaders (by bloc97, MIT License)?", default=True):
        from ...core.upscaling.anime4k import _download_anime4k_shaders
        with make_progress() as progress:
            task_id = progress.add_task("Downloading Anime4K shaders...", total=100)
            def _cb(pct, msg):
                progress.update(task_id, completed=pct, description=msg)
            try:
                _download_anime4k_shaders(progress_cb=_cb)
                ok("Anime4K shaders downloaded")
            except Exception as e:
                fail(str(e))
                raise typer.Exit(1)
    else:
        fail("Anime4K shaders are required for this method")
        raise typer.Exit(1)


def _ensure_ml_model(model_key, auto_yes=False):
    from ...core.upscaling.weight_loader import is_weight_downloaded, download_weights
    if is_weight_downloaded(model_key):
        return
    console.print(f"  [warn]Model '{model_key}' not downloaded.[/warn]")
    if auto_yes or typer.confirm(f"  Download {model_key}?", default=True):
        with make_progress() as progress:
            task_id = progress.add_task(f"Downloading {model_key}...", total=100)
            def _cb(pct, msg):
                progress.update(task_id, completed=pct, description=msg)
            if not download_weights(model_key, progress_cb=_cb):
                fail(f"Download failed for {model_key}")
                raise typer.Exit(1)
            ok(f"Model {model_key} downloaded")
    else:
        fail(f"Model {model_key} is required")
        raise typer.Exit(1)


def _ensure_artcnn_model(model_name, auto_yes=False):
    from ...core.upscaling.artcnn import _get_artcnn_dir, ARTCNN_MODELS
    info = ARTCNN_MODELS[model_name]
    path = os.path.join(_get_artcnn_dir(), info["file"])
    if os.path.exists(path):
        return
    console.print(f"  [warn]ArtCNN {model_name} not downloaded.[/warn]")
    if auto_yes or typer.confirm(f"  Download ArtCNN {model_name} (by Artoriuz)?", default=True):
        from ...core.upscaling.artcnn import _download_artcnn_model
        with make_progress() as progress:
            task_id = progress.add_task(f"Downloading ArtCNN {model_name}...", total=100)
            def _cb(pct, msg):
                progress.update(task_id, completed=pct, description=msg)
            try:
                _download_artcnn_model(model_name, progress_cb=_cb)
                ok(f"ArtCNN {model_name} downloaded")
            except Exception as e:
                fail(str(e))
                raise typer.Exit(1)
    else:
        fail(f"ArtCNN {model_name} is required")
        raise typer.Exit(1)


def upscale(
    input: Path = typer.Argument(None, help="Input video file"),
    output: Path = typer.Option(Path("upscaled.mp4"), "--output", "-o", help="Output video file"),
    method: str = typer.Option("ml", "--method", help="Upscale method: ml, anime4k, artcnn"),
    model: str = typer.Option("adore", "--model", "-m", help="ML model: adore, shufflecugan, fallin_soft, fallin_strong"),
    artcnn_model: str = typer.Option("C4F32", "--artcnn-model", help="ArtCNN model: C4F16, C4F32, R8F64"),
    anime4k_mode: str = typer.Option("medium", "--anime4k-mode", help="Anime4K mode: light, medium, strong"),
    scale: int = typer.Option(2, "--scale", "-s", help="Scale factor: 2 or 4"),
    preset: str = typer.Option("high", "--preset", "-p", help="Quality preset: archival, high, balanced, fast, draft"),
    fit_w: int = typer.Option(0, "--fit-w", help="Max output width (0 = no limit)"),
    fit_h: int = typer.Option(0, "--fit-h", help="Max output height (0 = no limit)"),
    credits: bool = typer.Option(False, "--credits", help="Show credits for upscaling technologies"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-confirm all download prompts"),
) -> None:
    """Upscale video using AI super-resolution.

    Methods:
      ml      - Neural network models (ShuffleCUGAN via PyTorch/spandrel). Based on AniSmooth.
      anime4k - GPU shader-based upscaler by bloc97. Fast, no ML deps.
      artcnn  - Lightweight CNN models by Artoriuz (via ONNX Runtime).

    Install: pip install amverge[upscale]
    """
    if credits:
        banner("upscale credits")
        console.print()
        for line in CREDITS_LINES:
            console.print(f"  [accent]+[/accent] {line}")
        console.print()
        console.print("  [dim]Anime4K: https://github.com/bloc97/Anime4K[/dim]")
        console.print("  [dim]ArtCNN:  https://github.com/Artoriuz/ArtCNN[/dim]")
        console.print("  [dim]AniSmooth: https://github.com/moongetsu/AniSmooth[/dim]")
        return

    if input is None:
        fail("Missing INPUT argument.")
        raise typer.Exit(1)
    if not input.exists():
        fail(f"File not found: {input}")
        raise typer.Exit(1)

    if method not in UPSCALE_METHODS:
        fail(f"Unknown method '{method}'. Valid: {', '.join(UPSCALE_METHODS)}")
        raise typer.Exit(1)
    if scale not in UPSCALE_SCALES:
        fail(f"Scale must be 2 or 4, got {scale}")
        raise typer.Exit(1)
    if preset not in UPSCALE_PRESETS:
        fail(f"Unknown preset '{preset}'. Valid: {', '.join(UPSCALE_PRESETS)}")
        raise typer.Exit(1)

    banner("upscale")

    if method == "anime4k":
        if anime4k_mode not in ANIME4K_MODES:
            fail(f"Unknown Anime4K mode '{anime4k_mode}'. Valid: {', '.join(ANIME4K_MODES)}")
            raise typer.Exit(1)

        _ensure_ffmpeg(auto_yes=yes)
        _ensure_anime4k_shaders(auto_yes=yes)

        from ...core.upscaling.anime4k import upscale_video_anime4k

        console.print(f"  Method: [accent]Anime4K[/accent] (shader-based, no ML deps)")
        console.print(f"  Mode: [accent]{anime4k_mode}[/accent]  "
                      f"Scale: [accent]{scale}x[/accent]  "
                      f"Preset: [accent]{preset}[/accent]")
        console.print(f"  Input: [dim]{input}[/dim]")
        console.print(f"  Output: [dim]{output}[/dim]")

        with make_progress() as progress:
            task_id = progress.add_task("Upscaling...", total=100)
            def _progress_cb(pct, msg):
                progress.update(task_id, completed=pct, description=msg)

            try:
                upscale_video_anime4k(
                    str(input.resolve()),
                    str(output.resolve()),
                    scale=scale,
                    mode=anime4k_mode,
                    preset=preset,
                    fit_w=fit_w,
                    fit_h=fit_h,
                    progress_cb=_progress_cb,
                )
            except Exception as e:
                fail(str(e))
                raise typer.Exit(1)

    elif method == "artcnn":
        if artcnn_model not in ARTCNN_MODEL_NAMES:
            fail(f"Unknown ArtCNN model '{artcnn_model}'. Valid: {', '.join(ARTCNN_MODEL_NAMES)}")
            raise typer.Exit(1)

        _ensure_ffmpeg(auto_yes=yes)
        _ensure_artcnn_model(artcnn_model, auto_yes=yes)

        from ...core.upscaling.artcnn import upscale_video_artcnn

        console.print(f"  Method: [accent]ArtCNN[/accent] (ONNX Runtime)")
        console.print(f"  Model: [accent]{artcnn_model}[/accent]  "
                      f"Scale: [accent]{scale}x[/accent]  "
                      f"Preset: [accent]{preset}[/accent]")
        console.print(f"  Input: [dim]{input}[/dim]")
        console.print(f"  Output: [dim]{output}[/dim]")

        with make_progress() as progress:
            task_id = progress.add_task("Upscaling...", total=100)
            def _progress_cb(pct, msg):
                progress.update(task_id, completed=pct, description=msg)

            try:
                upscale_video_artcnn(
                    str(input.resolve()),
                    str(output.resolve()),
                    model_name=artcnn_model,
                    scale=scale,
                    preset=preset,
                    fit_w=fit_w,
                    fit_h=fit_h,
                    progress_cb=_progress_cb,
                )
            except Exception as e:
                fail(str(e))
                raise typer.Exit(1)

    else:
        if model not in UPSCALE_MODELS:
            fail(f"Unknown model '{model}'. Valid: {', '.join(UPSCALE_MODELS)}")
            raise typer.Exit(1)

        _ensure_ffmpeg(auto_yes=yes)
        _ensure_ml_model(model, auto_yes=yes)

        try:
            from ...core.upscaling import UPSCALE_AVAILABLE, upscale_video
        except ImportError:
            fail("Upscaling module not available. Dependencies missing.")
            raise typer.Exit(1)

        if not UPSCALE_AVAILABLE:
            fail("ML upscaling requires torch and opencv. Run: pip install amverge[upscale]")
            raise typer.Exit(1)

        gpu_info = get_gpu_info()
        if gpu_info.get("cuda_available"):
            console.print(f"  GPU: [accent]{gpu_info.get('gpu_name', 'N/A')}[/accent]  "
                          f"VRAM: [accent]{gpu_info.get('gpu_memory_free_mb', 0)}/{gpu_info.get('gpu_memory_total_mb', 0)} MB[/accent]")
        else:
            console.print("  [warn]No NVIDIA GPU detected. Upscaling on CPU will be very slow.[/warn]")

        console.print(f"  Model: [accent]{model}[/accent]  "
                      f"Scale: [accent]{scale}x[/accent]  "
                      f"Preset: [accent]{preset}[/accent]")
        console.print(f"  Input: [dim]{input}[/dim]")
        console.print(f"  Output: [dim]{output}[/dim]")

        with make_progress() as progress:
            task_id = progress.add_task("Upscaling...", total=100)
            def _progress_cb(pct, msg):
                progress.update(task_id, completed=pct, description=msg)

            try:
                upscale_video(
                    str(input.resolve()),
                    str(output.resolve()),
                    model_name=model,
                    scale=scale,
                    preset=preset,
                    fit_w=fit_w,
                    fit_h=fit_h,
                    progress_cb=_progress_cb,
                )
            except Exception as e:
                fail(str(e))
                raise typer.Exit(1)

    ok(f"Upscaled video saved to {output}")
