<p align="center">
  <img src="../../AMVerge-CLI.gif" alt="AMVerge CLI" width="1440"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/pypi-amverge-22c55e?style=flat-square" alt="PyPI"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-22c55e?style=flat-square" alt="License"/>
</p>

# Export Examples

**Export selected scenes from a detect run.**  
Stream copy (lossless) or re-encode with full codec profile, audio, and hardware acceleration support.

---

## How It Works

```txt
scenes.json (from detect)
     ↓
select scenes by index
     ↓
ffmpeg copy (lossless) or re-encode (codec + audio + hardware)
     ↓
.mp4 / .mkv / .mov clips or merged file
```

When copying, video and audio streams pass through unchanged. When re-encoding,
choose from 15 codec profiles, 10 audio codecs, and optional GPU acceleration.

---

## Codec Profiles

| Shortcut | Maps To |
|---|---|
| `h264` | `h264_main` |
| `hevc` / `h265` | `h265_main` |

Full list in [CLI Reference](../../docs/cli-reference.md#amverge-export).

---

## Examples

| File | Description |
|---|---|
| [01_copy_export.py](01_copy_export.py) | stream copy, lossless |
| [02_reencode_export.py](02_reencode_export.py) | re-encode with codec/audio/hardware |
| [03_merge_export.py](03_merge_export.py) | merge selected scenes into one file |

---

## Quick Start

```bash
pip install amverge

# First run detection to get scenes.json
amverge detect episode.mp4

# Lossless copy
python examples/export/01_copy_export.py episode.mp4 episode_scenes/scenes.json

# Re-encode with profile
python examples/export/02_reencode_export.py episode.mp4 episode_scenes/scenes.json

# Merge into one file
python examples/export/03_merge_export.py episode.mp4 episode_scenes/scenes.json
```

---

## See Also

| | |
|---|---|
| [Library API](../../docs/library.md) | `CODEC_PROFILES`, `AUDIO_FFMPEG` |
| [CLI Reference](../../docs/cli-reference.md) | `amverge export` command |
