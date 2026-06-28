# TODO

Goal: users should never need to import external libraries directly.
Everything exposed through `from amverge import X` with clean classes/functions.

---

## 1. Video Reading / Encoding

Users currently need to understand PyAV, ffprobe args, subprocess ffmpeg commands.

### `AmvergeVideo` class

Wrap video I/O in a single class. Users should do:

```python
from amverge import AmvergeVideo

video = AmvergeVideo("episode.mp4")
print(video.duration, video.fps, video.width, video.height)
print(video.codec, video.is_hevc)
print(video.keyframes[:5])

frames = video.decode_frames()  # numpy array for TransNetV2
video.cut_scene(0.0, 5.0, "output.mp4")
video.extract_segment(0.0, 5.0, "segment.mp4")
video.extract_thumbnail(0.0, "thumb.jpg")
```

Replaces scattered imports:
- `get_video_duration()`, `get_video_info()` (core/video.py)
- `probe_video_fps()`, `probe_video_dimensions()`, `probe_video_duration()` (core/probe_utils.py)
- `check_if_hevc()`, `is_hevc()` (core/codec_utils.py, core/hevc.py)
- `get_keyframe_timestamps_pyav()`, `generate_keyframes()` (core/keyframe_align.py, core/keyframes.py)
- `decode_video_frames_nelux()`, `decode_and_detect_scenes()` (core/scene_detection.py)
- `make_thumbnail()`, `generate_thumbnails()` (core/thumbnails.py)
- `cut_scene()`, `cut_all_scenes()` (core/smart_cut.py)

---

## 2. Scene Detection

### `SceneDetector` class

```python
from amverge import SceneDetector

detector = SceneDetector(method="transnetv2")
result = detector.detect("episode.mp4")

# Or on an existing video object:
video = AmvergeVideo("episode.mp4")
result = video.detect_scenes(method="keyframe")
```

Wraps: `detect_scenes()`, `detect_cuts_by_keyframe()`, `detect_cuts_by_edge()`, V2 pipeline.

### `DetectResult` improvements

```python
result.scenes          # list[Scene]
result.similar_pairs   # list of similar pairs
result.json            # path to scenes.json
result.duration        # total video duration
result.detection_time  # how long detection took

result.to_dict()
result.to_json(path)
result.filter(min_duration=1.0)
result.merge_similar(threshold=0.05)
```

---

## 3. Export / Encoding

### `SceneExporter` class

```python
from amverge import SceneExporter

exporter = SceneExporter(
    codec="h264_main",
    audio="aac_320",
    container="mp4",
    hardware="auto",
)

exporter.export(scenes, output_dir="./export")
exporter.export_one(scene, "output.mp4")
exporter.merge(scenes, "merged.mp4")
```

Wraps: manual ffmpeg concat, `CODEC_PROFILES`, `AUDIO_FFMPEG`, `resolve_gpu()`.

---

## 4. Similarity / Comparison

### `SimilarityChecker` class

```python
from amverge import SimilarityChecker

checker = SimilarityChecker(threshold=0.10)
similar = checker.are_similar("thumb_a.jpg", "thumb_b.jpg")
pairs = checker.find_in(scenes)
```

Wraps: `check_pair_similar()`, `find_similar_pairs()`.

---

## 5. Image Operations

### `ImageCrop` class (rename from CropData)

```python
from amverge import ImageCrop

crop = ImageCrop(x=10, y=10, width=200, height=200, rotation=90)
crop.apply("input.jpg", "output.jpg")
crop.apply("input.gif", "output.gif")  # animated GIF support
```

Wraps: `CropData`, `crop_image()`. Rename `CropData` → `ImageCrop` for consistency.

---

## 6. Diagnostics

Already done: `get_gpu_info()`, `get_versions()`.

### Missing: `check_environment()`

```python
from amverge import check_environment

result = check_environment()
# result.passed: bool
# result.checks: list[CheckResult]
# result.summary: str
```

Wraps `amverge doctor` logic. Already exists in commands/doctor.py.

---

## 7. Thumbnails

### `ThumbnailGenerator` class

```python
from amverge import ThumbnailGenerator

gen = ThumbnailGenerator(workers=4)
gen.generate(scenes, output_dir="./thumbs")
gen.generate_one("clip.mp4", "thumb.jpg")
```

Wraps: `make_thumbnail()`, `generate_thumbnails()`.

---

## 8. Cache Management

### `SceneCache` class

```python
from amverge import SceneCache

cache = SceneCache("./cache_dir")
cache.list()
cache.clear("episode.mp4")
cache.clear_all()
cache.exists("episode.mp4")
cache.load("episode.mp4")  # returns (scenes_secs, scenes_frames) or None
cache.save("episode.mp4", scenes_secs, scenes_frames)
```

Wraps: `build_video_cache_prefix()`, manual .npy file I/O.

---

## 9. TransNetV2 Constants

Already exported: `FRAME_WIDTH`, `FRAME_HEIGHT`, etc. Consider wrapping:

```python
from amverge import TransNetConfig

config = TransNetConfig()
print(config.input_size)     # (48, 27)
print(config.window_size)    # 100
print(config.stride)         # 50
```

---

## 10. Remove Deep Imports from Examples

Current examples that still use non-top-level imports:

- `examples/export/02_reencode_export.py`: uses `from amverge import CODEC_PROFILES` (fixed - now top-level)
- `examples/custom-pipeline/full_pipeline.py`: uses direct `import torch`, `import numpy as np` - should use `AmvergeVideo` or helper functions

---

## Priority Order

1. `AmvergeVideo` class - biggest impact, wraps 10+ functions
2. `SceneDetector` class - wraps all detection logic
3. `SceneExporter` class - wraps codec/audio/encoding
4. `SceneCache` class - wraps .npy cache management
5. `ThumbnailGenerator` class - wraps thumbnail generation
6. `SimilarityChecker` class - wraps pair comparison
7. `ImageCrop` rename - consistency
8. `check_environment()` - wrap doctor logic
9. `TransNetConfig` class - constants wrapper
10. Clean up remaining examples
