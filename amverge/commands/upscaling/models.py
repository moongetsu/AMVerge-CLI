from __future__ import annotations

import os
from typing import Optional

import typer

from ...ui import banner, console, make_table, ok, fail, dim
from ...core.infra.config import get_models_dir
from ...core.upscaling.registry import (
    UPSCALE_REGISTRY, get_ml_models, get_shader_models, get_onnx_models, get_all_model_keys,
)
from ...core.upscaling.weight_loader import (
    WEIGHTS_DIR, get_weight_path, is_weight_downloaded, download_weights,
)


def _format_size(size_bytes):
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


def _list_ml_weights():
    entries = []
    for key, entry in get_ml_models().items():
        path = get_weight_path(key)
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        hash_val = entry.get("hash", "")[:12] if entry.get("hash") else "-"
        entries.append((key, entry["file"], _format_size(size) if exists else "-", hash_val, exists))
    return entries


def _list_onnx_weights():
    entries = []
    artcnn_dir = os.path.join(get_models_dir(), "artcnn")
    for key, entry in get_onnx_models().items():
        path = os.path.join(artcnn_dir, entry["file"])
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        entries.append((key, entry["file"], _format_size(size) if exists else "-", "-", exists))
    return entries


def _list_shaders():
    import glob
    shader_dir = os.path.join(get_models_dir(), "anime4k")
    if not os.path.exists(shader_dir):
        return [("anime4k", "no shaders", "0 B", "not downloaded", False)]
    glsl_files = glob.glob(os.path.join(shader_dir, "*.glsl"))
    total_size = sum(os.path.getsize(f) for f in glsl_files)
    exists = len(glsl_files) > 0
    entry = get_shader_models().get("anime4k", {})
    source = entry.get("credit", "bloc97/Anime4K")
    return [(entry.get("name", "Anime4K"), f"{len(glsl_files)} shaders",
             _format_size(total_size), source, exists)]


def _download_shaders(progress_cb=None):
    import urllib.request
    import ssl
    import zipfile

    entry = get_shader_models().get("anime4k", {})
    url = entry.get("download_url", "")
    if not url:
        raise RuntimeError("No download URL for anime4k")

    dest_dir = os.path.join(get_models_dir(), "anime4k")
    os.makedirs(dest_dir, exist_ok=True)
    zip_path = os.path.join(dest_dir, "Anime4K_v4.0.zip")

    ctx = ssl._create_unverified_context()

    if not os.path.exists(zip_path):
        req = urllib.request.Request(url, headers={"User-Agent": "amverge/1.0"})
        with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 65536
            with open(zip_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb and total > 0:
                        pct = min(99, int(downloaded * 100 / total))
                        progress_cb(pct, f"Downloading shaders... {pct}%")

    if progress_cb:
        progress_cb(100, "Extracting shaders...")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)

    import glob
    return [os.path.basename(p) for p in glob.glob(os.path.join(dest_dir, "*.glsl"))]


def _download_onnx_model(model_key, progress_cb=None):
    import urllib.request
    import ssl

    entry = get_onnx_models().get(model_key)
    if not entry:
        raise ValueError(f"Unknown ONNX model: {model_key}")

    artcnn_dir = os.path.join(get_models_dir(), "artcnn")
    os.makedirs(artcnn_dir, exist_ok=True)
    dest_path = os.path.join(artcnn_dir, entry["file"])

    if os.path.exists(dest_path):
        return

    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(entry["url"], headers={"User-Agent": "amverge/1.0"})
    with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 65536
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb and total > 0:
                    pct = min(99, int(downloaded * 100 / total))
                    progress_cb(pct, f"Downloading {model_key}... {pct}%")


def models(
    delete: Optional[str] = typer.Option(None, "--delete", help="Delete a model by key"),
    download: Optional[str] = typer.Option(None, "--download", help="Download a model by key"),
    show_storage: bool = typer.Option(False, "--storage", help="Show storage location"),
) -> None:
    """Manage upscaling model files.

    Without options, lists all downloaded models and their sizes.
    Use --delete to remove a model, --download to fetch one.
    """
    banner("models")

    if show_storage:
        console.print(f"  Models directory: [dim]{WEIGHTS_DIR}[/dim]")
        console.print(f"  Anime4K shaders:   [dim]{os.path.join(get_models_dir(), 'anime4k')}[/dim]")
        console.print(f"  ArtCNN models:     [dim]{os.path.join(get_models_dir(), 'artcnn')}[/dim]")
        console.print(f"  FFmpeg:            [dim]{os.path.dirname(os.path.dirname(WEIGHTS_DIR))}/ffmpeg/bin[/dim]")
        return

    if delete:
        if delete in get_ml_models():
            path = get_weight_path(delete)
            if os.path.exists(path):
                os.unlink(path)
                ok(f"Deleted model: {delete}")
            else:
                fail(f"Model not found on disk: {delete}")
        elif delete == "anime4k":
            import glob
            shader_dir = os.path.join(get_models_dir(), "anime4k")
            deleted = 0
            if os.path.exists(shader_dir):
                for fp in glob.glob(os.path.join(shader_dir, "*.glsl")):
                    os.unlink(fp)
                    deleted += 1
            ok(f"Deleted {deleted} shader files")
        elif delete in get_onnx_models():
            entry = get_onnx_models()[delete]
            path = os.path.join(get_models_dir(), "artcnn", entry["file"])
            if os.path.exists(path):
                os.unlink(path)
                ok(f"Deleted ONNX model: {delete}")
            else:
                fail(f"ONNX model not found: {delete}")
        else:
            fail(f"Unknown model key: {delete}")
            raise typer.Exit(1)
        return

    if download:
        if download in get_ml_models():
            entry = get_ml_models()[download]
            console.print(f"  Downloading [accent]{entry.get('name', download)}[/accent]...")
            success = download_weights(download)
            if success:
                ok(f"Downloaded: {download}")
            else:
                fail(f"Download failed for {download}")
        elif download == "anime4k":
            console.print("  Downloading [accent]Anime4K shaders[/accent]...")
            shaders = _download_shaders()
            ok(f"Downloaded {len(shaders)} shader files")
        elif download in get_onnx_models():
            entry = get_onnx_models()[download]
            console.print(f"  Downloading [accent]{entry.get('name', download)}[/accent]...")
            _download_onnx_model(download)
            ok(f"Downloaded ONNX model: {download}")
        else:
            fail(f"Unknown model key: {download}")
            raise typer.Exit(1)
        return

    console.print()
    console.print("  [white bold]ML Models[/white bold] [dim](PyTorch / spandrel)[/dim]")
    console.print()
    ml_entries = _list_ml_weights()
    table = make_table(("Model", "bright_black", {}), ("File", "bright_black", {}),
                       ("Size", "bright_black", {}), ("Hash", "bright_black", {}),
                       ("Status", "bright_black", {}), title=None)
    for key, filename, size, hash_short, exists in ml_entries:
        status = "[accent]downloaded[/accent]" if exists else "[muted]not downloaded[/muted]"
        table.add_row(f"[bold]{key}[/bold]", filename, size, f"{hash_short}...", status)
    console.print(table)

    console.print()
    console.print("  [white bold]Shader Upscaler[/white bold]")
    console.print()
    shader_entries = _list_shaders()
    table2 = make_table(("Name", "bright_black", {}), ("Files", "bright_black", {}),
                        ("Size", "bright_black", {}), ("Source", "bright_black", {}),
                        ("Status", "bright_black", {}), title=None)
    for name, files_str, size, source, exists in shader_entries:
        status = "[accent]downloaded[/accent]" if exists else "[muted]not downloaded[/muted]"
        table2.add_row(f"[bold]{name}[/bold]", files_str, size, source, status)
    console.print(table2)

    console.print()
    console.print("  [white bold]ONNX Models[/white bold] [dim](ArtCNN)[/dim]")
    console.print()
    onnx_entries = _list_onnx_weights()
    table3 = make_table(("Model", "bright_black", {}), ("File", "bright_black", {}),
                        ("Size", "bright_black", {}), ("Hash", "bright_black", {}),
                        ("Status", "bright_black", {}), title=None)
    for name, filename, size, hash_short, exists in onnx_entries:
        status = "[accent]downloaded[/accent]" if exists else "[muted]not downloaded[/muted]"
        table3.add_row(f"[bold]{name}[/bold]", filename, size, f"{hash_short}", status)
    console.print(table3)

    console.print()
    all_keys = get_all_model_keys()
    console.print(f"  [dim]Use --download <key> to download, --delete <key> to remove[/dim]")
    console.print(f"  [dim]Keys: {', '.join(all_keys)}[/dim]")
