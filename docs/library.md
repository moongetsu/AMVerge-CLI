# Python Library

AMVerge CLI is fully usable as a Python library. The high-level API covers most use cases; low-level modules are available for custom pipelines.

---

## Quick Start

```python
from amverge import detect_scenes

result = detect_scenes("episode.mp4")

for scene in result.scenes:
    print(scene.index, scene.start, scene.end, scene.path)

for a, b in result.similar_pairs:
    print(f"Scenes {a} and {b} look similar - consider merging")
```

---

## `detect_scenes()`

```python
from amverge import detect_scenes, DetectResult

# Keyframe detection (default, no extra deps)
result: DetectResult = detect_scenes("episode.mp4")

# Edge detection (needs pip install amverge[edge])
result = detect_scenes("episode.mp4", method="edge")

# TransNetV2 ML detection (needs pip install amverge[ml])
result = detect_scenes("episode.mp4", method="transnetv2")

# Full options
result = detect_scenes(
    video_path="episode.mp4",
    output_dir="./scenes",         # defaults to <name>_scenes/ next to video
    method="keyframe",              # "keyframe" | "edge" | "transnetv2"
    min_duration=0.25,              # merge scenes shorter than N seconds
    thumbnails=True,                # generate JPEG thumbnails
    similarity=True,                # flag adjacent scenes that look similar
    similarity_threshold=0.10,      # lower = stricter
    thumbnail_workers=4,
    edge_threshold=0.15,            # edge method only
    edge_radius=0.6,                # edge method only
    progress=lambda stage, pct, msg: print(f"[{stage}] {pct}% {msg}"),
)
```

---

## Return Types

```python
from dataclasses import dataclass

@dataclass
class Scene:
    index: int
    start: float          # seconds from video start
    end: float            # seconds from video start
    duration: float       # seconds
    path: str             # absolute path to the .mp4 clip
    thumbnail: str | None # absolute path to the .jpg thumbnail (None if skipped)
    original_file: str    # stem of the source video

@dataclass
class DetectResult:
    scenes: list[Scene]
    similar_pairs: list[tuple[int, int]]  # (scene_index_a, scene_index_b)
    output_dir: str
    scenes_json: str      # path to the saved scenes.json file
```

---

## Progress Callback

Pass a callable to `progress` to receive live updates:

```python
def on_progress(stage: str, pct: int, msg: str) -> None:
    # stage: "detect" | "segment" | "thumbnails" | "similarity"
    # pct: 0-100
    print(f"[{stage}] {pct}%  {msg}")

result = detect_scenes("episode.mp4", progress=on_progress)
```

---

## Low-Level Modules

### Binary resolution

```python
from amverge.core.binaries import get_ffmpeg, get_ffprobe

ffmpeg_path  = get_ffmpeg()   # raises if not found
ffprobe_path = get_ffprobe()
```

### Keyframe extraction

```python
from amverge.core.keyframes import generate_keyframes

timestamps: list[float] = generate_keyframes("video.mp4")
```

Uses PyAV packet demux (fast path) with a decode fallback for pathological encodes.

### Video metadata

```python
from amverge.core.video import get_video_duration, get_video_info

duration: float = get_video_duration("video.mp4")
info: dict = get_video_info("video.mp4")
# info["duration"], info["streams"] -> list of video/audio stream dicts
```

### ffprobe helpers

```python
from amverge.core.probe_utils import (
    probe_video_duration,
    probe_video_fps,
    probe_video_dimensions,
    probe_video_total_frames,
)

fps = probe_video_fps("video.mp4")
w, h = probe_video_dimensions("video.mp4")
```

### Scene segmentation (V1 - keyframe/edge)

```python
from amverge.core.segmenter import run_ffmpeg_segment, collect_scenes

run_ffmpeg_segment("video.mp4", "output_%04d.mp4", cut_points)
scenes = collect_scenes("output_dir", "video_stem")
```

Handles Windows 32,767-char command line limit via 1500-cut chunking.

### Smart cut (V2 - TransNetV2)

```python
from amverge.core.smart_cut import cut_scene, cut_all_scenes
from amverge.core.keyframe_align import get_keyframe_timestamps_pyav, classify_scenes_by_keyframe_alignment
from amverge.core.codec_utils import check_if_hevc

keyframes = get_keyframe_timestamps_pyav("video.mp4")
is_hevc = check_if_hevc("video.mp4")

results = cut_all_scenes(
    input_file=Path("video.mp4"),
    scenes=[{"scene_index": 0, "start_sec": 0.0, "end_sec": 5.0}],
    keyframes=keyframes,
    out_dir=Path("./scenes"),
    use_cuda=True,
    is_hevc=is_hevc,
    max_workers=8,
    on_ready=lambda r: print(r["scene_index"], r["clip_mode"]),
)
```

### TransNetV2 scene detection

```python
from amverge.core.scene_detection import (
    decode_and_detect_scenes,     # FFmpeg pipe decode + inference (cross-platform)
    decode_video_frames_nelux,    # Nelux Windows native decode (optional)
    run_model_one_pass,           # inference on pre-decoded frame array
)

# One-shot: decode + detect in one call
scenes_secs, scenes_frames = decode_and_detect_scenes("video.mp4")

# Or step by step (for custom pipelines)
frames = decode_video_frames_nelux("video.mp4")  # numpy array (N, 27, 48, 3)
scenes_secs, scenes_frames = run_model_one_pass(frames, "video.mp4")
```

Requires `pip install amverge[ml]`. Raises clear `ImportError` if missing.

### Keyframe alignment

```python
from amverge.core.keyframe_align import (
    get_keyframe_timestamps_pyav,
    classify_scenes_by_keyframe_alignment,
)

keyframes = get_keyframe_timestamps_pyav("video.mp4")
# [0.0, 0.5, 1.0, 1.5, ...]

scene_pairs = [(0.0, 5.0), (5.1, 10.0)]
copy_candidates, reencode_candidates = classify_scenes_by_keyframe_alignment(
    scene_pairs, keyframes
)
# copy: scenes starting on a keyframe
# reencode: scenes needing smartcut or full re-encode
```

### Scene utilities

```python
from amverge.core.scene_utils import scenes_to_objects, scenes_frames_to_seconds
import numpy as np

# Convert frame-based scenes to seconds
secs = scenes_frames_to_seconds(np.array([[0, 120], [120, 240]]), fps=24.0)
# [[0.0, 5.0], [5.0, 10.0]]

# Build scene dicts with metadata
scenes = scenes_to_objects(scenes_secs=secs, scenes_frames=np.array([[0, 120], [120, 240]]))
# [{"scene_index": 0, "start_sec": 0.0, "end_sec": 5.0, ...}, ...]
```

### Thumbnails

```python
from amverge.core.thumbnails import make_thumbnail, generate_thumbnails

make_thumbnail("clip.mp4", "thumbnail.jpg")
generate_thumbnails(scenes, output_dir="./scenes", file_name="episode", workers=4)
```

### Similarity

```python
from amverge.core.similarity import check_pair_similar, find_similar_pairs

similar: bool = check_pair_similar("thumb_a.jpg", "thumb_b.jpg", threshold=0.10)
pairs: list[tuple[int, int]] = find_similar_pairs(scenes, threshold=0.10)
```

Uses cosine similarity on average-pooled pixel arrays. Accepts `scene_index` or `index` key in scene dicts.

### HEVC detection

```python
from amverge.core.codec_utils import check_if_hevc

check_if_hevc("video.mp4")  # True / False
```

### Image crop

```python
from amverge.core.image import crop_image, CropData

crop_image(
    "input.jpg", "output.jpg",
    CropData(x=10, y=10, width=200, height=200, rotation=90),
)
```

Supports animated GIF input/output.

### IPC events

```python
from amverge.core.ipc import emit_progress, emit_event, log

emit_progress(50, "Halfway done")
emit_event("CLIP_READY|0|path/to/clip.mp4|copy")
log("Custom log message")
```

### Discord RPC

```python
from amverge.core.discord_rpc import DiscordRPC, RPC_AVAILABLE

if RPC_AVAILABLE:
    rpc = DiscordRPC()
    rpc.connect()
    rpc.update_detecting("episode.mp4")
    rpc.clear_presence()
    rpc.disconnect()
```
