<p align="center">
  <img src="../../assets/amverge_title_gif.gif" alt="AMVerge CLI" width="1440"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/pypi-amverge-22c55e?style=flat-square" alt="PyPI"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-22c55e?style=flat-square" alt="License"/>
</p>

# Keyframe Examples

**Extract I-frame timestamps and classify scenes for cutting.**  
Keyframes mark positions where lossless stream copy is possible.
Scenes starting on a keyframe can be copied; others need re-encoding.

---

## How It Works

```txt
video file
     ↓
PyAV packet demux (Discard.nonkey)
     ↓
sorted keyframe timestamps (seconds)
     ↓
classify scene boundaries against keyframes
     ↓
copy candidates (lossless) / re-encode candidates
```

The V1 method (`generate_keyframes`) supports progress callbacks.
The V2 method (`get_keyframe_timestamps_pyav`) uses PyAV 17.x enum API.

---

## Examples

| File | Description |
|---|---|
| [01_extract_keyframes.py](01_extract_keyframes.py) | V1 + V2 keyframe extraction with stats |
| [02_align_scenes.py](02_align_scenes.py) | classify scenes for lossless copy vs re-encode |

---

## Quick Start

```bash
pip install amverge

# Extract keyframes
python examples/keyframes/01_extract_keyframes.py episode.mp4

# Align sample scenes
python examples/keyframes/02_align_scenes.py episode.mp4
```

---

## See Also

| | |
|---|---|
| [Library API](../../docs/library.md) | `get_keyframe_timestamps_pyav()`, `classify_scenes_by_keyframe_alignment()` |
| [Detection Methods](../../docs/detection-methods.md) | how keyframes drive the cut pipeline |
