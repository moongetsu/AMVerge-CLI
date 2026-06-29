<p align="center">
  <img src="assets/AMVerge-CLI.gif" alt="AMVerge CLI" width="1440"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python"/>
  <a href="https://pypi.org/project/amverge/"><img src="https://img.shields.io/badge/pypi-amverge-22c55e?style=flat-square" alt="PyPI"/></a>
  <img src="https://img.shields.io/badge/license-GPL--3.0-22c55e?style=flat-square" alt="License"/>
</p>

# AMVerge CLI

**AMVerge Features as a CLI Tool and Python Library.**
Port of the AMVerge desktop app backend by [Crptk](https://github.com/crptk). Split videos into scenes, export clips, merge fragments, and build your own tools on top of it.

---

## Features

- **TransNetV2 ML detection** - deep learning scene boundary detection (GPU/CPU)
- **Keyframe detection** - fast I-frame based splitting, no re-encode
- **Edge detection** - Canny edges + cosine similarity for difficult encodes
- **Smart cut** - automatic lossless copy / smartcut / re-encode per scene
- **15 codec profiles** - H.264, HEVC, AV1, ProRes with hardware (NVENC) support
- **10 audio codecs** - AAC, FLAC, Opus, PCM, MP3, pass-through
- **3 container formats** - MP4, MKV, MOV (ProRes auto-enforces MOV)
- Auto-generated scene thumbnails (progressive JPEG)
- Duplicate / similar scene detection (cosine similarity)
- Scene export with full codec + audio + hardware selection
- Clip merging via FFmpeg concat
- Video metadata inspection and diagnostics
- TransNetV2 scene cache (.npy) - skip re-detection on re-open
- Discord Rich Presence (same app ID as AMVerge desktop)
- Interactive wizard mode (`amverge` with no args)
- Fully usable as a Python library - 52 names from `import amverge`

---

## Install

```bash
pip install amverge
```

See [docs/installation.md](docs/installation.md) for FFmpeg setup, optional dependencies, and dev install.

---

## Quick Start

```bash
# Interactive wizard
amverge

# Direct commands
amverge detect episode.mp4
amverge export episode.mp4 --scenes episode_scenes/scenes.json --select 0,2,5-8
amverge merge clip1.mp4 clip2.mp4 --output out.mp4
amverge info episode.mp4
```

```python
from amverge import detect_scenes

result = detect_scenes("episode.mp4")
for scene in result.scenes:
    print(scene.index, scene.start, scene.end, scene.path)
```

---

<details open>
<summary><b>How It Works</b></summary>

```txt
amverge CLI  /  Python library
          ↓
   amverge package
          ↓
    PyAV  +  FFmpeg  +  PyTorch (optional)
```

**Detection:** Keyframe mode extracts I-frame timestamps via PyAV packet demux.
Edge mode decodes frames and compares Canny edge maps.
TransNetV2 runs a deep CNN on 48x27 RGB frames (GPU auto-detected, CPU fallback).

**Cutting:** Scenes aligned to keyframes get lossless stream copy.
Non-aligned scenes get smartcut (encode head + copy tail) or full re-encode.
HEVC on CPU uses snapped-copy (nearest keyframe within 5s) to avoid slow re-encode.

**Thumbnails:** Decoded via PyAV, resized to 960px, saved as progressive JPEG in parallel.
**Similarity:** Adjacent thumbnails compared via cosine similarity on 8x8 pooled pixels.

</details>

---

<details>
<summary><b>Repository Structure</b></summary>

```txt
AMVerge-CLI/
├── amverge/
│   ├── __init__.py              public exports: detect_scenes, DetectResult, Scene, DetectionMethod
│   ├── __version__.py           version string
│   ├── cli.py                   Typer app, registers commands, no-args -> wizard
│   ├── pipeline.py              high-level detect_scenes() API
│   ├── wizard.py                interactive session (no-args mode)
│   ├── ui.py                    shared Rich theme, console, banner, progress, table helpers
│   │
│   ├── commands/                one file per CLI subcommand
│   │   ├── about.py             about
│   │   ├── backend.py           backend (hidden - Rust sidecar replacement)
│   │   ├── bench.py             bench (keyframe scan + TransNetV2 timing)
│   │   ├── cache.py             cache (list/clear .npy scene caches)
│   │   ├── changelog.py         changelog
│   │   ├── credits.py           credits
│   │   ├── detect.py            detect
│   │   ├── doctor.py            doctor (full health check)
│   │   ├── export.py            export (codec profiles + hardware selection)
│   │   ├── gpu.py               gpu (CUDA, GPU name/VRAM)
│   │   ├── info.py              info (stream metadata via PyAV)
│   │   ├── keyframes.py         keyframes (dump keyframe timestamps)
│   │   ├── merge.py             merge
│   │   ├── probe.py             probe (codec/HEVC/keyframes/scene cache)
│   │   ├── rpc_server.py        rpc-server (hidden - Discord RPC sidecar)
│   │   ├── scenes.py            scenes (show scene list from .npy cache)
│   │   ├── usage.py             usage (CLI reference page)
│   │   └── version.py           version (CLI + Python + dep versions)
│   │
│   └── core/                    pure logic, no CLI/Rich deps
│       ├── binaries.py          get_binary(), get_ffmpeg(), get_ffprobe()
│       ├── codec_utils.py       check_if_hevc(), CODEC_PROFILES, AUDIO_FFMPEG
│       ├── diagnostics.py       get_gpu_info(), get_versions()
│       ├── discord_rpc.py       DiscordRPC class (pypresence wrapper)
│       ├── hevc.py              is_hevc() (V1 codec check)
│       ├── image.py             crop_image() + CropData
│       ├── ipc.py               emit_progress(), emit_event(), log()
│       ├── keyframe_align.py    get_keyframe_timestamps_pyav(), classify_scenes_by_keyframe_alignment()
│       ├── keyframes.py         generate_keyframes() (V1 packet demux)
│       ├── nelux_runtime.py     _get_nelux_video_reader() (Windows DLL config)
│       ├── probe_utils.py       probe_video_fps/duration/dimensions/total_frames
│       ├── scene_detection.py   decode_video_frames_nelux(), decode_and_detect_scenes(), run_model_one_pass()
│       ├── scene_utils.py       scenes_to_objects(), scenes_frames_to_seconds()
│       ├── segmenter.py         run_ffmpeg_segment() (1500-cut Windows chunking)
│       ├── similarity.py        find_similar_pairs() (cosine similarity)
│       ├── smart_cut.py         cut_scene(), cut_all_scenes() (lossless copy / smartcut / reencode)
│       ├── thumbnails.py        make_thumbnail(), generate_thumbnails() (ThreadPoolExecutor)
│       ├── thumbnails_streaming.py  streaming thumbnail gen with IPC events
│       ├── transnet_constants.py    FRAME_WIDTH/HEIGHT/CHANNELS, WINDOW_SIZE, STRIDE
│       ├── video.py             get_video_duration(), get_video_info(), merge_short_scenes()
│       └── detection/
│           ├── keyframe.py      detect_cuts_by_keyframe() (V1)
│           └── edge.py          detect_cuts_by_edge() (guarded cv2 import, V1)
│
├── examples/                runnable Python scripts
│   ├── custom-pipeline/     full end-to-end pipeline
│   ├── cutting/             smart cut, ffmpeg segment
│   ├── detect/              keyframe, edge, TransNetV2 detection
│   ├── diagnostics/         GPU, CUDA, dependency versions
│   ├── discord-rpc/         Discord Rich Presence
│   ├── export/              copy, re-encode with profiles, merge
│   ├── info-probe/          stream metadata, diagnostics, HEVC check
│   ├── keyframes/           extraction + classification for cutting
│   ├── similarity/          adjacent scene similarity detection
│   └── thumbnails/          JPEG thumbnail generation
│
├── docs/                    markdown documentation
├── assets/                  GIF and image assets
├── pyproject.toml
├── README.md
└── AGENTS.md
```

</details>

---

<details>
<summary><b>Examples</b></summary>

Runnable Python scripts for every feature. Each with its own README:

| Directory | Description |
|---|---|
| [detect/](examples/detect/) | keyframe, edge, TransNetV2 detection |
| [export/](examples/export/) | copy, re-encode with profiles, merge |
| [info-probe/](examples/info-probe/) | stream metadata, probe diagnostics, HEVC check |
| [keyframes/](examples/keyframes/) | extract timestamps, classify for cutting |
| [cutting/](examples/cutting/) | smart cut, ffmpeg segment, single scene |
| [thumbnails/](examples/thumbnails/) | JPEG thumbnail generation |
| [similarity/](examples/similarity/) | adjacent scene similarity detection |
| [diagnostics/](examples/diagnostics/) | GPU, CUDA, dependency versions |
| [discord-rpc/](examples/discord-rpc/) | Discord Rich Presence |
| [custom-pipeline/](examples/custom-pipeline/) | full end-to-end custom pipeline |

```bash
pip install amverge[ml,edge,discord]
python examples/detect/01_basic_detect.py episode.mp4
python examples/custom-pipeline/full_pipeline.py episode.mp4
```

See the [examples README](examples/README.md) for the full directory map.

</details>

---

<details>
<summary><b>Documentation</b></summary>

| | |
|---|---|
| [Installation](docs/installation.md) | Requirements, FFmpeg setup, optional deps, dev install |
| [CLI Reference](docs/cli-reference.md) | All commands, flags, and usage examples |
| [Python Library](docs/library.md) | API reference, return types, low-level modules |
| [Detection Methods](docs/detection-methods.md) | Keyframe vs edge vs TransNetV2, cut modes, tuning |
| [Examples](examples/) | 20 runnable Python scripts in 10 categories |
| [Contributing](docs/contributing.md) | Project structure, guidelines, links |
| [AI Setup](docs/ai-setup.md) | How to train AI tools to work like you, not generically |

</details>

---

<details>
<summary><b>AI Agents</b></summary>

An [AGENTS.md](AGENTS.md) file is included for AI coding assistants (OpenCode, Claude Code, Cursor, etc.).

Using AI without understanding the codebase is not recommended. Read the code, understand the architecture, then use the agents file if it saves you time.

The best approach is not to use a generic AI assistant - it is to train it to work like you. Teach it your conventions, your decisions, your style. Done right, the output looks like yours, not like a generic answer. See [docs/ai-setup.md](docs/ai-setup.md) for a practical guide on how to do this.

</details>

---

<details>
<summary><b>Credits</b></summary>

Built by [Moongetsu](https://github.com/Moongetsu) as a standalone port of the [AMVerge](https://github.com/AMVerge-team/AMVerge) backend.

AMVerge was created by [Crptk](https://github.com/crptk). All core scene detection and clip management logic originates from the original AMVerge project.

</details>

---

<details>
<summary><b>License</b></summary>

AMVerge CLI is licensed under the GNU GPL v3.0.

Any derivative work must also be open-source under the same license.

</details>
