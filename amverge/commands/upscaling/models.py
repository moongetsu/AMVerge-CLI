from __future__ import annotations

import os
from typing import Optional

import typer

from ...ui import banner, console, make_table, ok, fail, dim
from ...core.upscaling.weight_loader import (
    WEIGHTS_DIR, MODEL_FILES, UPSCALE_MODEL_KEYS, MODEL_HASHES,
    get_weight_path, is_weight_downloaded, download_weights, verify_weight_hash,
)

MODEL_CATEGORIES = {
    "ml": ["adore", "shufflecugan", "fallin_soft", "fallin_strong"],
    "anime4k": ["anime4k_shaders"],
    "artcnn": ["C4F16", "C4F32", "R8F64"],
}


def _format_size(size_bytes):
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


def _list_ml_weights():
    entries = []
    for key in UPSCALE_MODEL_KEYS:
        path = get_weight_path(key)
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        hash_short = MODEL_HASHES.get(key, "")[:12] if MODEL_HASHES.get(key) else "-"
        entries.append((key, MODEL_FILES[key][1], _format_size(size) if exists else "-", hash_short, exists))
    return entries


def _list_artcnn_models():
    entries = []
    from ...core.upscaling.artcnn import _get_artcnn_dir, ARTCNN_MODELS
    artcnn_dir = _get_artcnn_dir()
    for name, info in ARTCNN_MODELS.items():
        path = os.path.join(artcnn_dir, info["file"])
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        entries.append((name, info["file"], _format_size(size) if exists else "-", info.get("sha256", "-") or "-", exists))
    return entries


def _list_anime4k_shaders():
    from ...core.upscaling.anime4k import _get_anime4k_dir
    import glob
    shader_dir = _get_anime4k_dir()
    if not os.path.exists(shader_dir):
        return [("Anime4K v4.0.1", "0/0 shaders", "0 B", "bloc97/Anime4K", False)]
    glsl_files = glob.glob(os.path.join(shader_dir, "*.glsl"))
    total_size = sum(os.path.getsize(f) for f in glsl_files)
    exists = len(glsl_files) > 0
    entries = [("Anime4K v4.0.1", f"{len(glsl_files)} shaders", _format_size(total_size), "bloc97/Anime4K", exists)]
    return entries


def models(
    delete: Optional[str] = typer.Option(None, "--delete", help="Delete a model by key (adore, shufflecugan, C4F32, anime4k)"),
    download: Optional[str] = typer.Option(None, "--download", help="Download a model by key"),
    show_storage: bool = typer.Option(False, "--storage", help="Show storage location"),
) -> None:
    """Manage upscaling model files.

    Without options, lists all downloaded models and their sizes.
    Use --delete to remove a model, --download to fetch one.
    """
    banner("models")

    if show_storage:
        console.print(f"  Weights directory: [dim]{WEIGHTS_DIR}[/dim]")
        from ...core.upscaling.anime4k import _get_anime4k_dir
        from ...core.upscaling.artcnn import _get_artcnn_dir
        console.print(f"  Anime4K shaders:   [dim]{_get_anime4k_dir()}[/dim]")
        console.print(f"  ArtCNN models:     [dim]{_get_artcnn_dir()}[/dim]")

    if delete:
        if delete in UPSCALE_MODEL_KEYS:
            path = get_weight_path(delete)
            if os.path.exists(path):
                os.unlink(path)
                ok(f"Deleted model: {delete}")
            else:
                fail(f"Model not found on disk: {delete}")
        elif delete.lower() == "anime4k":
            from ...core.upscaling.anime4k import _get_anime4k_dir
            import glob
            shader_dir = _get_anime4k_dir()
            deleted = 0
            if os.path.exists(shader_dir):
                for fp in glob.glob(os.path.join(shader_dir, "*.glsl")):
                    os.unlink(fp)
                    deleted += 1
            ok(f"Deleted {deleted} Anime4K shader files")
        elif delete in ("C4F16", "C4F32", "R8F64"):
            from ...core.upscaling.artcnn import _get_artcnn_dir, ARTCNN_MODELS
            info = ARTCNN_MODELS[delete]
            path = os.path.join(_get_artcnn_dir(), info["file"])
            if os.path.exists(path):
                os.unlink(path)
                ok(f"Deleted ArtCNN model: {delete}")
            else:
                fail(f"ArtCNN model not found on disk: {delete}")
        else:
            fail(f"Unknown model key: {delete}. Use: adore, shufflecugan, fallin_soft, fallin_strong, anime4k, C4F16, C4F32, R8F64")
            raise typer.Exit(1)
        return

    if download:
        if download in UPSCALE_MODEL_KEYS:
            console.print(f"  Downloading [accent]{download}[/accent]...")
            success = download_weights(download)
            if success:
                ok(f"Downloaded: {download}")
            else:
                fail(f"Download failed for {download}")
        elif download == "anime4k":
            from ...core.upscaling.anime4k import _download_anime4k_shaders
            console.print("  Downloading [accent]Anime4K shaders v4.0.1[/accent]...")
            shaders = _download_anime4k_shaders()
            ok(f"Downloaded {len(shaders)} Anime4K shader files")
        elif download in ("C4F16", "C4F32", "R8F64"):
            from ...core.upscaling.artcnn import _download_artcnn_model
            console.print(f"  Downloading [accent]ArtCNN {download}[/accent]...")
            _download_artcnn_model(download)
            ok(f"Downloaded ArtCNN model: {download}")
        else:
            fail(f"Unknown model key: {download}")
            raise typer.Exit(1)
        return

    console.print()
    console.print("  [white bold]ShuffleCUGAN Models[/white bold] [dim](based on AniSmooth)[/dim]")
    console.print()
    ml_entries = _list_ml_weights()
    table = make_table(("Model", "bright_black", {}), ("File", "bright_black", {}), ("Size", "bright_black", {}), ("Hash", "bright_black", {}), ("Status", "bright_black", {}), title=None)
    for key, filename, size, hash_short, exists in ml_entries:
        status = "[accent]downloaded[/accent]" if exists else "[muted]not downloaded[/muted]"
        table.add_row(f"[bold]{key}[/bold]", filename, size, f"{hash_short}...", status)
    console.print(table)

    console.print()
    console.print("  [white bold]Anime4K Shaders[/white bold] [dim](by bloc97)[/dim]")
    console.print()
    anime4k_entries = _list_anime4k_shaders()
    table2 = make_table(("Version", "bright_black", {}), ("Files", "bright_black", {}), ("Size", "bright_black", {}), ("Source", "bright_black", {}), ("Status", "bright_black", {}), title=None)
    for name, files_str, size, source, exists in anime4k_entries:
        status = "[accent]downloaded[/accent]" if exists else "[muted]not downloaded[/muted]"
        table2.add_row(f"[bold]{name}[/bold]", files_str, size, source, status)
    console.print(table2)

    console.print()
    console.print("  [white bold]ArtCNN Models[/white bold] [dim](by Artoriuz)[/dim]")
    console.print()
    artcnn_entries = _list_artcnn_models()
    table3 = make_table(("Model", "bright_black", {}), ("File", "bright_black", {}), ("Size", "bright_black", {}), ("Hash", "bright_black", {}), ("Status", "bright_black", {}), title=None)
    for name, filename, size, hash_short, exists in artcnn_entries:
        status = "[accent]downloaded[/accent]" if exists else "[muted]not downloaded[/muted]"
        table3.add_row(f"[bold]{name}[/bold]", filename, size, f"{hash_short}", status)
    console.print(table3)

    console.print()
    console.print("  [dim]Use --download <key> to download, --delete <key> to remove[/dim]")
    console.print("  [dim]Keys: adore, shufflecugan, fallin_soft, fallin_strong, anime4k, C4F16, C4F32, R8F64[/dim]")
