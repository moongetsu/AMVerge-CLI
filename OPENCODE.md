# AMVerge CLI - OpenCode Context

This file gives a full picture of what was built, where it came from, and every decision made.
Read this before touching anything.

---

## What This Is

A standalone Python CLI tool and library that ports the entire backend of the
[AMVerge](https://github.com/crptk/AMVerge) desktop app (by Crptk) into a
`pip install amverge` package.

Original AMVerge is a Tauri + React + Python desktop app for splitting anime episodes into
scenes, previewing them in a grid, and exporting selected clips. This repo extracts the
Python backend and wraps it in a proper CLI + public library API.

---

## Origin - Where the Code Came From

All core logic was ported from:
```
C:\Users\Moongetsu\Documents\GitHub\AMVergeNew\backend\
```

Key source files from the original:
- `backend/utils/keyframes.py` → `amverge_cli/core/keyframes.py`
- `backend/utils/video_utils.py` → `amverge_cli/core/video.py`
- `backend/utils/binaries.py` → `amverge_cli/core/binaries.py`
- `backend/app.py` → logic split across `pipeline.py` + `core/segmenter.py`
- `backend/utils/nelux_runtime.py` → `amverge_cli/core/detection/edge.py`
- `backend/utils/scene_detection_methods.py` → `amverge_cli/core/detection/keyframe.py`
- `backend/utils/smart_cut.py` → parts of `amverge_cli/core/similarity.py`

AMVerge app color palette from:
```
C:\Users\Moongetsu\Documents\GitHub\AMVergeNew\frontend\src\styles\variables.css
```
- Accent: `#22c55e`
- Accent bright: `#00f07a`
- Background tint: `#001a00`

---

## Project Structure

```
AMVerge-CLI/
├── amverge_cli/
│   ├── __init__.py         exports: detect_scenes, DetectResult, Scene, DetectionMethod
│   ├── __version__.py      version string: "0.1.0"
│   ├── cli.py              Typer app, registers all commands, no-args -> wizard
│   ├── pipeline.py         high-level detect_scenes() public API
│   ├── wizard.py           interactive session (runs when amverge called with no args)
│   ├── ui.py               shared Rich theme, console, banner, progress, table helpers
│   │
│   ├── commands/
│   │   ├── detect.py       amverge detect
│   │   ├── export.py       amverge export
│   │   ├── merge.py        amverge merge
│   │   ├── info.py         amverge info
│   │   ├── usage.py        amverge usage  (command reference)
│   │   ├── about.py        amverge about
│   │   ├── credits.py      amverge credits
│   │   └── changelog.py    amverge changelog
│   │
│   └── core/               pure logic - no CLI/Rich deps, safe to import as library
│       ├── binaries.py     get_ffmpeg(), get_ffprobe() - PATH then local bin/ fallback
│       ├── keyframes.py    generate_keyframes() - PyAV packet demux + decode fallback
│       ├── video.py        get_video_duration(), get_video_info(), merge_short_scenes()
│       ├── segmenter.py    run_ffmpeg_segment() - 1500-cut Windows chunking
│       ├── thumbnails.py   make_thumbnail(), generate_thumbnails() - ThreadPoolExecutor
│       ├── similarity.py   find_similar_pairs() - cosine similarity on pixel arrays
│       ├── hevc.py         is_hevc() - ffprobe codec check
│       ├── image.py        crop_image() + CropData - supports animated GIF
│       └── detection/
│           ├── keyframe.py detect_cuts_by_keyframe()
│           └── edge.py     detect_cuts_by_edge() - needs opencv, guarded import
│
├── docs/
│   ├── installation.md
│   ├── cli-reference.md
│   ├── library.md
│   ├── detection-methods.md
│   └── contributing.md
│
├── assets/
│   └── amverge_title_gif.gif   copied from AMVergeNew frontend assets
│
├── pyproject.toml          hatchling build, name="amverge", entry: amverge = cli:app
├── LICENSE                 GPL v3, copyright Moongetsu, credits Crptk
└── README.md
```

---

## How the CLI Works

```
amverge                   -> wizard (interactive session)
amverge detect video.mp4  -> direct execution
amverge --help            -> Typer built-in help
```

`cli.py` uses `@app.callback(invoke_without_command=True)` - when no subcommand is
passed, `ctx.invoked_subcommand is None` triggers `run_wizard()` from `wizard.py`.

---

## UI / Theme System

All output goes through `amverge_cli/ui.py`.

```python
THEME = Theme({
    "accent":        "#22c55e",
    "accent.bright": "#00f07a",
    "muted":         "bright_black",
    "success":       "#22c55e bold",
    "warn":          "#facc15",
    "error":         "#ef4444",
    "label":         "white",
    "bar.back":      "bright_black",
    "bar.complete":  "#22c55e",
    "bar.finished":  "#00f07a",
}, inherit=False)

console = Console(theme=THEME, highlight=False)       # stdout
err     = Console(theme=THEME, stderr=True, ...)      # stderr (wizard + banners)
```

**Critical:** Rich theme names (like `accent`) only resolve inside markup strings
`[accent]text[/]`. They do NOT work as `style=` parameters on Table/Column/etc.
Always use the literal hex `#22c55e bold` in style= positions.

Banner color split: `[accent]AMV[/][white bold]erge[/]` - AMV is green, erge is white.

Wizard uses `err` (stderr) for all interactive prompts so stdout stays clean for
piping. Direct commands use `banner()` which also prints to stderr.

---

## Wizard Structure

`wizard.py` has two command groups:

```python
_WORKFLOW = [detect, export, merge, info]     # numbered 01-04
_INFO     = [usage, about, credits,changelog] # numbered 05-08
```

Menu shows both groups separated by a blank row. User picks by number (`01`) or
name (`detect`). Each wizard function calls `_header()`, `_section()`, step-by-step
`_ask()` prompts, a `_summary_panel()` review, then runs the operation.

After each command: "press enter to continue" -> back to menu.

`_credits_table()` in `commands/credits.py` is shared by both the wizard and the
direct `amverge credits` command to avoid duplication.

---

## Key Technical Decisions

### 1500-cut Windows chunking (segmenter.py)
Windows has a 32,767 char command line limit. If a video has >1500 cut points,
`run_ffmpeg_segment()` chunks them and runs multiple ffmpeg passes. Ported directly
from the original AMVerge backend.

### PyAV packet demux for keyframes (keyframes.py)
Fast path: reads only packet metadata without decoding frames. Falls back to full
decode for pathological encodes. Also detects pathological files (too many keyframes
in a short window) and applies deduplication.

### Edge detection is optional (detection/edge.py)
OpenCV is not in the base dependencies. `detect_cuts_by_edge()` does
`import cv2` inside the function and raises a clear `ImportError` with
`pip install amverge[edge]` instructions if not present.

### core/ has no CLI deps
Everything in `core/` imports only stdlib + PyAV + numpy + pillow. No Rich, no Typer.
This keeps the library API clean for people building their own tools.

### CREATE_NO_WINDOW on Windows
All subprocess calls include `creationflags=0x08000000` on win32 to suppress
console windows from ffmpeg/ffprobe popups.

---

## Package / PyPI

```toml
[project]
name = "amverge"          # pip install amverge
version = "0.1.0"

[project.scripts]
amverge = "amverge_cli.cli:app"

[project.optional-dependencies]
edge = ["opencv-python-headless>=4.9"]
dev  = ["pyinstaller>=6"]
```

Not yet published to PyPI. To publish:
```bash
pip install build twine
python -m build
twine upload dist/*
```
Check `pypi.org/project/amverge` first to confirm name is free.

---

## Commit Style

Must match AniSmooth repo style - prefix in parentheses:

```
(add) description
(fix) description
(update) description
```

No `feat:` / `fix:` / conventional commits format. Parentheses only.

---

## Known Fixes Applied

- `accent bold` as `style=` on Rich Table/Column raises `MissingStyle` error.
  Fixed by replacing all `style="accent bold"` with `style="#22c55e bold"` everywhere.
  Theme names only work inside `[accent bold]markup[/]`, not in style= params.

- Em dashes (`-`) were replaced with hyphens (`-`) across all `.py` and `.md` files.

- The `credits` page originally used two separate `make_table()` calls which showed
  duplicate `name / role` headers. Fixed by using one custom Table with `end_section=True`
  separator rows for "AMVerge CLI" and "AMVerge App" sections.

---

## GitHub Repo

```
https://github.com/moongetsu/AMVerge-CLI
```

- Public, branch: `master`
- Description: "AMVerge Features as a CLI Tool and Python Library"
- License: GPL v3 (Moongetsu), credits Crptk as original AMVerge author
- Local path: `C:\Users\Moongetsu\Documents\GitHub\AMVerge-CLI`
- Original AMVerge local path: `C:\Users\Moongetsu\Documents\GitHub\AMVergeNew`

---

## What's Left / Possible Next Steps

- Publish to PyPI (`pip install amverge`)
- Terminal recording / GIF of the wizard for the README
- After Effects CEP extension that uses this as its backend
- `amverge update` command to check for new releases
- Progress callback improvements (ETA, speed)
- Windows installer / bundled ffmpeg
