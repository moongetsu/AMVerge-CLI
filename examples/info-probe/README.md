<p align="center">
  <img src="../../AMVerge-CLI.gif" alt="AMVerge CLI" width="1440"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/pypi-amverge-22c55e?style=flat-square" alt="PyPI"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-22c55e?style=flat-square" alt="License"/>
</p>

# Info & Probe Examples

**Inspect video metadata and diagnostics.**  
Get codec, resolution, FPS, bitrate, keyframe stats, and HEVC detection using PyAV and ffprobe.

---

## How It Works

```txt
video file
     ↓
PyAV open (container probe)
     ↓
stream metadata (codec, resolution, fps, channels)
     ↓
ffprobe (duration, exact fps, dimensions, HEVC check)
     ↓
keyframe extraction (PyAV packet demux)
```

No frame decoding required. All metadata gathered from container headers and packet-level reads.

---

## Examples

| File | Description |
|---|---|
| [01_video_info.py](01_video_info.py) | stream metadata via PyAV |
| [02_probe.py](02_probe.py) | ffprobe diagnostics (fps, duration, dimensions, keyframes) |
| [03_hevc_check.py](03_hevc_check.py) | HEVC codec detection |

---

## Quick Start

```bash
pip install amverge

# Stream metadata
python examples/info-probe/01_video_info.py episode.mp4

# Full probe diagnostics
python examples/info-probe/02_probe.py episode.mp4

# Check if HEVC encoded
python examples/info-probe/03_hevc_check.py episode.mp4
```

---

## See Also

| | |
|---|---|
| [Library API](../../docs/library.md) | `get_video_info()`, `check_if_hevc()` |
| [CLI Reference](../../docs/cli-reference.md) | `amverge info`, `amverge probe` |
