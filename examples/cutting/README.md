<p align="center">
  <img src="../../assets/AMVerge-CLI.gif" alt="AMVerge CLI" width="1440"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/pypi-amverge-22c55e?style=flat-square" alt="PyPI"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-22c55e?style=flat-square" alt="License"/>
</p>

# Scene Cutting Examples

**Cut video into clips using smart cut or FFmpeg segment muxer.**  
Automatic mode selection: lossless copy when possible, smartcut/re-encode when needed.

---

## How It Works

```txt
scene boundaries + keyframes
     ↓
check start alignment with keyframe
     ↓
┌─────────────────────────────────────┐
│ on keyframe     → copy (lossless)   │
│ HEVC, kf < 5s   → snapped_copy     │
│ H.264, kf < 90% → smartcut         │
│ fallback        → reencode         │
└─────────────────────────────────────┘
     ↓
parallel cut via ThreadPoolExecutor
```

The V1 pipeline uses `ffmpeg -segment_times` with stream copy for lossless splitting.
The V2 pipeline uses `cut_all_scenes` with automatic four-mode smart cut.

---

## Examples

| File | Description |
|---|---|
| [01_smart_cut.py](01_smart_cut.py) | V2 pipeline: automatic mode selection |
| [02_ffmpeg_segment.py](02_ffmpeg_segment.py) | V1 pipeline: FFmpeg segment muxer |
| [03_single_scene.py](03_single_scene.py) | cut one scene, inspect chosen mode |

---

## Quick Start

```bash
pip install amverge[ml]

# Smart cut (V2)
python examples/cutting/01_smart_cut.py episode.mp4

# FFmpeg segment (V1)
python examples/cutting/02_ffmpeg_segment.py episode.mp4

# Single scene test
python examples/cutting/03_single_scene.py episode.mp4
```

---

## See Also

| | |
|---|---|
| [Library API](../../docs/library.md) | `cut_scene()`, `cut_all_scenes()`, `run_ffmpeg_segment()` |
| [Detection Methods](../../docs/detection-methods.md) | cut mode comparison table |
