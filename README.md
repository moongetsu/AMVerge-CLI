# AMVerge CLI

Scene detection and clip management — usable as a CLI tool or a Python library.

## Install

```bash
pip install amverge-cli

# For edge-detection method (requires OpenCV):
pip install amverge-cli[edge]
```

Requires **ffmpeg** and **ffprobe** on your PATH (or in the working directory).

---

## Python Library API

### Quick start

```python
from amverge_cli import detect_scenes

result = detect_scenes("episode.mp4")

for scene in result.scenes:
    print(scene.index, scene.start, scene.end, scene.path)

for a, b in result.similar_pairs:
    print(f"Scenes {a} and {b} look similar — consider merging")
```

### `detect_scenes()`

```python
from amverge_cli import detect_scenes, DetectResult

result: DetectResult = detect_scenes(
    video_path="episode.mp4",
    output_dir="./scenes",       # defaults to <name>_scenes/ next to video
    method="keyframe",            # "keyframe" (fast) or "edge" (accurate, needs OpenCV)
    min_duration=0.25,            # merge scenes shorter than N seconds
    thumbnails=True,              # generate JPEG thumbnails
    similarity=True,              # flag adjacent scenes that look similar
    similarity_threshold=0.10,    # lower = stricter similarity
    thumbnail_workers=4,
    # edge method options:
    edge_threshold=0.15,
    edge_radius=0.6,
    edge_blocksize=3,
    # optional progress callback:
    progress=lambda stage, pct, msg: print(f"[{stage}] {pct}% {msg}"),
)
```

### Return types

```python
@dataclass
class Scene:
    index: int
    start: float          # seconds
    end: float            # seconds
    duration: float       # seconds
    path: str             # absolute path to the .mp4 clip
    thumbnail: str | None # absolute path to the .jpg thumbnail
    original_file: str    # stem of the source video

@dataclass
class DetectResult:
    scenes: list[Scene]
    similar_pairs: list[tuple[int, int]]  # (scene_index_a, scene_index_b)
    output_dir: str
    scenes_json: str      # path to the saved scenes.json file
```

### Low-level modules

```python
# Binary resolution
from amverge_cli.core.binaries import get_ffmpeg, get_ffprobe

# Keyframe extraction
from amverge_cli.core.keyframes import generate_keyframes
timestamps = generate_keyframes("video.mp4")

# Video metadata
from amverge_cli.core.video import get_video_duration, get_video_info
info = get_video_info("video.mp4")  # codec, resolution, fps, bitrate

# FFmpeg segmenter
from amverge_cli.core.segmenter import run_ffmpeg_segment, collect_scenes

# Thumbnails
from amverge_cli.core.thumbnails import make_thumbnail, generate_thumbnails

# Similarity
from amverge_cli.core.similarity import check_pair_similar, find_similar_pairs

# HEVC detection
from amverge_cli.core.hevc import is_hevc
is_hevc("video.mp4")  # True / False

# Image crop (supports GIF)
from amverge_cli.core.image import crop_image, CropData
crop_image("in.jpg", "out.jpg", CropData(x=10, y=10, width=200, height=200, rotation=90))

# Detection methods
from amverge_cli.core.detection import detect_cuts_by_keyframe, detect_cuts_by_edge
cut_points = detect_cuts_by_keyframe("video.mp4", min_duration=0.25)
cut_points = detect_cuts_by_edge("video.mp4", threshold=0.15)  # needs [edge]
```

---

## CLI Commands

### `amverge detect`

```bash
amverge detect video.mp4
amverge detect video.mp4 --output ./scenes --method edge
amverge detect video.mp4 --format json > scenes.json
amverge detect video.mp4 --no-thumbnails --no-similarity
amverge detect video.mp4 --min-duration 0.5 --workers 8
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output / -o` | `<name>_scenes/` | Output directory |
| `--method / -m` | `keyframe` | `keyframe` or `edge` |
| `--format / -f` | `table` | `table`, `json`, or `paths` |
| `--json-output` | — | Also save JSON to a file |
| `--no-thumbnails` | false | Skip thumbnail generation |
| `--no-similarity` | false | Skip similarity check |
| `--min-duration` | `0.25` | Merge scenes shorter than N seconds |
| `--workers` | `4` | Thumbnail worker threads |
| `--similarity-threshold` | `0.10` | Similarity cutoff |
| `--edge-threshold` | `0.15` | Edge detection sensitivity |
| `--edge-radius` | `0.6` | Keyframe window radius (edge method) |

### `amverge export`

```bash
amverge export video.mp4 --scenes scenes.json --output ./export
amverge export video.mp4 --scenes scenes.json --select 0,2,5-8
amverge export video.mp4 --scenes scenes.json --select 0-10 --merge
amverge export video.mp4 --scenes scenes.json --codec h264
```

| Flag | Default | Description |
|------|---------|-------------|
| `--scenes / -s` | required | `scenes.json` from `detect` |
| `--output / -o` | `./export` | Output directory |
| `--select` | all | Indices: `0,2,5-8` |
| `--merge` | false | Merge into one file |
| `--codec` | `copy` | `copy`, `h264`, `hevc` |

### `amverge merge`

```bash
amverge merge clip1.mp4 clip2.mp4 clip3.mp4 --output merged.mp4
```

### `amverge info`

```bash
amverge info video.mp4
```

---

## Detection Methods

| Method | Speed | Accuracy | Requirement |
|--------|-------|----------|-------------|
| `keyframe` | Fast | Cuts only at I-frames | PyAV (base install) |
| `edge` | Slow | Frame-accurate via Canny edges | OpenCV (`pip install amverge-cli[edge]`) |

Use `keyframe` for most anime and broadcast content where scenes always start at keyframes.
Use `edge` for heavily compressed files or content where keyframe placement is unreliable.
