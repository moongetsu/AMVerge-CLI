# CLI Reference

Run `amverge` with no arguments to open the interactive wizard.  
Run `amverge --help` to see all commands.

---

## Workflow Commands

### `amverge detect`

Split a video into scenes at cut boundaries.

```bash
amverge detect episode.mp4
amverge detect episode.mp4 --output ./scenes --method edge
amverge detect episode.mp4 --format json > scenes.json
amverge detect episode.mp4 --no-thumbnails --no-similarity
amverge detect episode.mp4 --min-duration 0.5 --workers 8
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output / -o` | `<name>_scenes/` | Output directory |
| `--method / -m` | `keyframe` | `keyframe` or `edge` |
| `--format / -f` | `table` | `table`, `json`, or `paths` |
| `--json-output` | - | Also save JSON to a file |
| `--no-thumbnails` | false | Skip thumbnail generation |
| `--no-similarity` | false | Skip similarity check |
| `--min-duration` | `0.25` | Merge scenes shorter than N seconds |
| `--workers` | `4` | Thumbnail thread count |
| `--similarity-threshold` | `0.10` | Similarity cutoff (lower = stricter) |
| `--edge-threshold` | `0.15` | Edge detection sensitivity |
| `--edge-radius` | `0.6` | Keyframe window radius (edge method) |

**Output:** a folder containing `.mp4` scene clips, `.jpg` thumbnails, and a `scenes.json` index.

---

### `amverge export`

Export selected scenes from a previous detect run.

```bash
amverge export episode.mp4 --scenes episode_scenes/scenes.json
amverge export episode.mp4 --scenes scenes.json --output ./export
amverge export episode.mp4 --scenes scenes.json --select 0,2,5-8
amverge export episode.mp4 --scenes scenes.json --select 0-10 --merge
amverge export episode.mp4 --scenes scenes.json --codec h264
```

| Flag | Default | Description |
|------|---------|-------------|
| `--scenes / -s` | required | `scenes.json` from `detect` |
| `--output / -o` | `./export` | Output directory |
| `--select` | all | Index range: `0,2,5-8` |
| `--merge` | false | Merge selection into one file |
| `--codec` | `copy` | `copy`, `h264`, `hevc` |

**Codec options:**

- `copy` - stream copy, no re-encode, no quality loss (fastest)
- `h264` - re-encode to H.264 + AAC
- `hevc` - re-encode to HEVC/H.265 + AAC

---

### `amverge merge`

Merge multiple clips into a single file using FFmpeg concat.

```bash
amverge merge clip1.mp4 clip2.mp4 clip3.mp4 --output merged.mp4
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output / -o` | required | Output file path |

---

### `amverge info`

Show video and audio stream metadata.

```bash
amverge info episode.mp4
```

Displays codec, resolution, FPS, bitrate, sample rate, and channel count.

---

## Info Commands

```bash
amverge usage      # command reference and examples
amverge about      # what AMVerge CLI is
amverge credits    # contributors
amverge changelog  # version history
```

---

## Interactive Wizard

Running `amverge` with no arguments opens a full interactive session.  
Each command walks through its options step by step with a summary before running.

```bash
amverge
```
