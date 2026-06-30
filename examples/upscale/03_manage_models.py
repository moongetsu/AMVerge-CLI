import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from amverge import (
    MODEL_FILES, UPSCALE_MODEL_KEYS, ARTCNN_MODELS,
    is_weight_downloaded, download_weights, get_weight_path,
)

print("=== ML Models (ShuffleCUGAN, based on AniSmooth) ===")
for key in UPSCALE_MODEL_KEYS:
    _, filename = MODEL_FILES[key]
    path = get_weight_path(key)
    exists = is_weight_downloaded(key)
    size = Path(path).stat().st_size if exists else 0
    status = "downloaded" if exists else "not downloaded"
    print(f"  {key:16s} {filename:35s} {size / (1024*1024):.1f} MB  [{status}]")

print()
print("=== ArtCNN Models (by Artoriuz) ===")
for name, info in ARTCNN_MODELS.items():
    from amverge.core.upscaling.artcnn import _get_artcnn_dir
    path = Path(_get_artcnn_dir()) / info["file"]
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    status = "downloaded" if exists else "not downloaded"
    print(f"  {name:8s} {info['file']:25s} {size / (1024*1024):.1f} MB  [{status}]")

print()
print("=== Anime4K Shaders (by bloc97) ===")
from amverge import ANIME4K_SHADER_FILES
from amverge.core.upscaling.anime4k import _get_anime4k_dir
shader_dir = Path(_get_anime4k_dir())
if shader_dir.exists():
    count = sum(1 for f in shader_dir.iterdir() if f.suffix == ".glsl")
    size = sum(f.stat().st_size for f in shader_dir.iterdir() if f.is_file())
    print(f"  {count}/{len(ANIME4K_SHADER_FILES)} shaders downloaded ({size / 1024:.1f} KB)")
else:
    print(f"  No shaders downloaded. Use: amverge models --download anime4k")

if len(sys.argv) > 1 and sys.argv[1] == "--download":
    print()
    print("Downloading all models...")
    for key in UPSCALE_MODEL_KEYS:
        if not is_weight_downloaded(key):
            download_weights(key)
            print(f"  {key}: downloaded")
        else:
            print(f"  {key}: already cached")
