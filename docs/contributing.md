# Contributing

Contributions are welcome. Bug fixes, new features, and improvements to detection accuracy are all fair game.

---

## Setup

```bash
git clone https://github.com/AMVerge-team/AMVerge-CLI
cd AMVerge-CLI
pip install -e ".[ml,edge,discord]"
```

---

## Project Structure

```txt
amverge/
├── __init__.py              public exports: detect_scenes, DetectResult, Scene, DetectionMethod
├── __version__.py           version string
├── cli.py                   Typer app, registers commands, no-args -> wizard
├── pipeline.py              high-level detect_scenes() API
├── wizard.py                interactive session (no-args mode)
├── ui.py                    shared Rich theme, console, banner, progress, table helpers
│
├── commands/
│   ├── about/               about, credits, changelog, usage
│   ├── detection/           detect, bench, cache, scenes, keyframes
│   ├── export/              export, merge
│   ├── info/                info, probe
│   ├── sidecar/             backend, rpc_server (hidden)
│   └── system/              doctor, gpu, version
│
├── core/                    pure logic, no CLI/Rich deps
│   ├── codec/               codec profiles, HEVC detection
│   ├── cutting/             segmenter (V1), smart_cut (V2)
│   ├── detection/           keyframe, edge (V1), scene_detection, nelux_runtime (V2)
│   ├── discord/             Discord RPC integration
│   ├── image/               image cropping
│   ├── infra/               binaries, IPC, diagnostics
│   ├── keyframes/           keyframe extraction + alignment
│   ├── similarity/          cosine similarity pair detection
│   ├── thumbnails/          thumbnail generation + streaming
│   ├── transnet/            TransNetV2 constants
│   ├── video/               probe_utils, scene_utils, video metadata
│   └── wrappers/            public class wrappers (AmvergeVideo, SceneDetector, etc.)
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

---

## Guidelines

- Keep `core/` modules free of CLI/Rich dependencies
- New CLI commands go in the appropriate `commands/` subdirectory (`detection/`, `export/`, `info/`, `system/`, `about/`, `sidecar/`), register in `cli.py`, add to wizard in `wizard.py`
- Match the existing commit style: `(add)`, `(fix)`, `(update)` prefix
- One commit per logical change
- No code comments unless asked
- No em dashes in prose or commit messages
- Update `AGENTS.md` when adding/removing files or changing architecture

---

## Links

- Main repo: [github.com/AMVerge-team/AMVerge](https://github.com/AMVerge-team/AMVerge)
- Discord: [discord.gg/bmXjTgsAaN](https://discord.gg/bmXjTgsAaN)
