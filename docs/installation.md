# Installation

## Requirements

- Python 3.11+
- `ffmpeg` and `ffprobe` on your PATH (or dropped in the working directory)

---

## Install

```bash
pip install amverge
```

That's it for the base install. Covers `detect` (keyframe method), `export`, `merge`, and `info`.

---

## Edge Detection (Optional)

The `edge` detection method requires OpenCV:

```bash
pip install amverge[edge]
```

Only needed if you plan to use `--method edge`. See [detection-methods.md](detection-methods.md) for when it's worth it.

---

## FFmpeg

AMVerge CLI looks for `ffmpeg` / `ffprobe` in this order:

1. System PATH
2. A `bin/` folder in the current working directory

If neither is found, commands that require FFmpeg will fail with a clear error.

Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) or install via your package manager:

```bash
# Windows (winget)
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

---

## Development Install

Clone and install in editable mode:

```bash
git clone https://github.com/moongetsu/AMVerge-CLI
cd AMVerge-CLI
pip install -e .

# With edge support:
pip install -e ".[edge]"
```
