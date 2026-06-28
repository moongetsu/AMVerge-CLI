<p align="center">
  <img src="../../assets/amverge_title_gif.gif" alt="AMVerge CLI" width="1440"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/pypi-amverge-22c55e?style=flat-square" alt="PyPI"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-22c55e?style=flat-square" alt="License"/>
</p>

# Thumbnail Examples

**Generate JPEG thumbnails from video clips.**  
Extracts the first keyframe, resizes to 960px wide, and saves as progressive JPEG at 95% quality.

---

## How It Works

```txt
clip .mp4 file
     ↓
PyAV open + skip to first keyframe
     ↓
decode one frame
     ↓
resize to 960px wide (Lanczos)
     ↓
save as progressive JPEG, quality 95
```

Parallel generation via `ThreadPoolExecutor`. Workers capped at CPU count.

---

## Examples

| File | Description |
|---|---|
| [01_make_thumbnails.py](01_make_thumbnails.py) | single thumbnail + batch generation |

---

## Quick Start

```bash
pip install amverge

# Generate thumbnails from clips
python examples/thumbnails/01_make_thumbnails.py episode.mp4
```

---

## See Also

| | |
|---|---|
| [Library API](../../docs/library.md) | `make_thumbnail()`, `generate_thumbnails()` |
