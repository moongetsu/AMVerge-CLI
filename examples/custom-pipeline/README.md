<p align="center">
  <img src="../../assets/amverge_title_gif.gif" alt="AMVerge CLI" width="1440"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/pypi-amverge-22c55e?style=flat-square" alt="PyPI"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-22c55e?style=flat-square" alt="License"/>
</p>

# Custom Pipeline Example

**Full end-to-end detection and cutting from scratch.**  
Replicates `amverge detect --method transnetv2` step by step using only the low-level library API.
Modify any step to build your own custom workflow.

---

## How It Works

```txt
video file
     ↓
[1] TransNetV2 decode + inference  (scene_detection.py)
     ↓
[2] keyframe timestamps            (keyframe_align.py)
     ↓
[3] HEVC check                     (codec_utils.py)
     ↓
[4] build scene objects            (scene_utils.py)
     ↓
[5] classify by keyframe alignment (keyframe_align.py)
     ↓
[6] Phase 1: lossless copy         (smart_cut.py, 8 workers)
    Phase 2: smartcut / re-encode  (smart_cut.py, 2 workers)
     ↓
[7] thumbnails + similarity check  (thumbnails.py, similarity.py)
     ↓
JSON manifest + metadata
```

Each step uses a separate low-level module. Swap any step to change the behavior.

---

## Examples

| File | Description |
|---|---|
| [full_pipeline.py](full_pipeline.py) | 7-step custom pipeline end-to-end |

---

## Quick Start

```bash
pip install amverge[ml]

python examples/custom-pipeline/full_pipeline.py episode.mp4
```

---

## See Also

| | |
|---|---|
| [Library API](../../docs/library.md) | all low-level modules used |
| [Detection Methods](../../docs/detection-methods.md) | TransNetV2 cut modes |
