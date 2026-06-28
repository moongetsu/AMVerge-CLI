"""Interactive wizard session — launched when amverge is run with no arguments."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.rule import Rule

from .ui import banner, console, err, make_progress, make_table, ok, fail, dim, THEME
from .__version__ import __version__


# ---------------------------------------------------------------------------
# Styled prompt helpers
# ---------------------------------------------------------------------------

def _prompt(label: str, default: str = "", password: bool = False) -> str:
    hint = f"[muted][{default}][/muted] " if default else ""
    return Prompt.ask(
        f"  [accent]›[/] [label]{label}[/] {hint}",
        console=err,
        default=default,
        password=password,
    ).strip()


def _prompt_path(label: str, default: str = "", must_exist: bool = False) -> str:
    while True:
        raw = _prompt(label, default)
        if not raw:
            raw = default
        if must_exist and raw and not Path(raw).exists():
            err.print(f"  [error]✗[/] not found: {raw}")
            continue
        return raw


def _confirm(label: str, default: bool = True) -> bool:
    hint = "[muted][Y/n][/muted]" if default else "[muted][y/N][/muted]"
    return Confirm.ask(
        f"  [accent]›[/] [label]{label}[/] {hint}",
        console=err,
        default=default,
    )


def _float_prompt(label: str, default: float, lo: float, hi: float) -> float:
    while True:
        raw = _prompt(label, str(default))
        try:
            v = float(raw)
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        err.print(f"  [error]✗[/] enter a number between {lo} and {hi}")


def _int_prompt(label: str, default: int, lo: int, hi: int) -> int:
    while True:
        raw = _prompt(label, str(default))
        try:
            v = int(raw)
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        err.print(f"  [error]✗[/] enter an integer between {lo} and {hi}")


def _choice(label: str, choices: list[str], default: str) -> str:
    opts = " · ".join(f"[accent]{c}[/]" if c == default else c for c in choices)
    err.print(f"  [accent]›[/] [label]{label}[/]  {opts}")
    while True:
        raw = _prompt("", default).lower()
        if raw in choices:
            return raw
        err.print(f"  [error]✗[/] choose: {' / '.join(choices)}")


# ---------------------------------------------------------------------------
# Command wizards
# ---------------------------------------------------------------------------

def _wizard_detect() -> None:
    from .pipeline import detect_scenes, DetectResult

    err.print()
    err.print(Rule("[accent]detect[/]", style="muted"))
    err.print()

    video = _prompt_path("video path", must_exist=True)
    if not video:
        return
    output = _prompt_path("output dir", "[auto]")
    output = None if output in ("", "[auto]") else output

    method = _choice("method", ["keyframe", "edge"], "keyframe")
    min_dur = _float_prompt("min duration (s)", 0.25, 0.01, 60.0)
    thumbs = _confirm("generate thumbnails", True)
    similarity = _confirm("check similarity", True) if thumbs else False
    workers = _int_prompt("thumbnail workers", 4, 1, 32) if thumbs else 4

    err.print()
    err.print(Rule(style="muted"))
    err.print()

    _LABELS = {
        "detect": "Detecting cuts",
        "segment": "Cutting scenes",
        "thumbnails": "Thumbnails",
        "similarity": "Similarity check",
    }

    with make_progress() as progress:
        tasks: dict[str, object] = {}

        def on_progress(stage: str, pct: int, msg: str) -> None:
            label = _LABELS.get(stage, stage)
            if stage not in tasks:
                tasks[stage] = progress.add_task(label, total=100)
            progress.update(tasks[stage], completed=pct, description=label)

        result: DetectResult = detect_scenes(
            video,
            output_dir=output,
            method=method,
            min_duration=min_dur,
            thumbnails=thumbs,
            similarity=similarity,
            thumbnail_workers=workers,
            progress=on_progress,
        )

    if not result.scenes:
        fail("No scenes detected.")
        return

    similar_set = {idx for pair in result.similar_pairs for idx in pair}

    t = make_table(
        ("#",        "muted", {"justify": "right", "width": 5}),
        ("Start",    None,    {"justify": "right", "width": 9}),
        ("End",      None,    {"justify": "right", "width": 9}),
        ("Duration", None,    {"justify": "right", "width": 9}),
        ("~",        "warn",  {"justify": "center", "width": 3}),
        title=f"{Path(video).stem}  ·  {len(result.scenes)} scenes  ·  {method}",
    )
    for s in result.scenes:
        t.add_row(
            str(s.index),
            f"{s.start:.2f}s",
            f"{s.end:.2f}s",
            f"{s.duration:.2f}s",
            "~" if s.index in similar_set else "",
        )
    console.print(t)
    dim(f"scenes.json → {result.scenes_json}")


def _wizard_export() -> None:
    import subprocess
    import tempfile
    from .core.binaries import get_ffmpeg

    err.print()
    err.print(Rule("[accent]export[/]", style="muted"))
    err.print()

    scenes_path = _prompt_path("scenes.json path", must_exist=True)
    if not scenes_path:
        return

    payload = json.loads(Path(scenes_path).read_text())
    all_scenes: list[dict] = payload.get("scenes", payload) if isinstance(payload, dict) else payload

    if not all_scenes:
        fail("No scenes in JSON.")
        return

    max_idx = max(s["scene_index"] for s in all_scenes)
    err.print(f"  [muted]{len(all_scenes)} scenes available (0–{max_idx})[/]")
    err.print()

    select = _prompt("select indices (e.g. 0,2,5-8 or blank for all)", "")
    if select:
        indices: set[int] = set()
        for part in select.split(","):
            part = part.strip()
            if "-" in part:
                lo, hi = part.split("-", 1)
                indices.update(range(int(lo), int(hi) + 1))
            else:
                indices.add(int(part))
        selected = [s for s in all_scenes if s["scene_index"] in indices]
    else:
        selected = all_scenes

    if not selected:
        fail("No scenes matched.")
        return

    output = _prompt_path("output dir", "export")
    merge = _confirm("merge into one file", False)
    codec = _choice("codec", ["copy", "h264", "hevc"], "copy")

    output_path = Path(output or "export")
    output_path.mkdir(parents=True, exist_ok=True)
    ff = get_ffmpeg()
    CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

    err.print()
    err.print(Rule(style="muted"))
    err.print()

    if merge:
        with make_progress() as progress:
            task = progress.add_task(f"Merging {len(selected)} clips", total=1)
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                concat_file = f.name
                for s in selected:
                    f.write(f"file '{s['path'].replace(chr(92), '/')}'\n")
            dst = str(output_path / "merged.mp4")
            try:
                cmd = [ff, "-y", "-f", "concat", "-safe", "0", "-i", concat_file]
                cmd += ["-c", "copy"] if codec == "copy" else ["-c:v", codec, "-c:a", "aac"]
                cmd.append(dst)
                subprocess.run(cmd, capture_output=True, creationflags=CREATE_NO_WINDOW, check=True)
            finally:
                os.unlink(concat_file)
            progress.update(task, completed=1)
        ok(f"Merged → {dst}")
    else:
        with make_progress(show_count=True) as progress:
            task = progress.add_task(f"Exporting {len(selected)} clips", total=len(selected))
            for s in selected:
                idx = s["scene_index"]
                dst = str(output_path / f"scene_{idx:04d}.mp4")
                if codec == "copy":
                    subprocess.run([ff, "-y", "-i", s["path"], "-c", "copy", dst],
                                   capture_output=True, creationflags=CREATE_NO_WINDOW, check=True)
                else:
                    subprocess.run([ff, "-y", "-i", s["path"], "-c:v", codec, "-c:a", "aac", dst],
                                   capture_output=True, creationflags=CREATE_NO_WINDOW, check=True)
                progress.advance(task)
        ok(f"{len(selected)} clips → {output_path}")


def _wizard_merge() -> None:
    import subprocess
    import tempfile
    from .core.binaries import get_ffmpeg

    err.print()
    err.print(Rule("[accent]merge[/]", style="muted"))
    err.print()

    err.print("  [muted]Enter clip paths one by one. Empty line when done.[/]")
    clips: list[Path] = []
    while True:
        raw = _prompt(f"clip {len(clips) + 1}", "")
        if not raw:
            break
        p = Path(raw)
        if not p.exists():
            err.print(f"  [error]✗[/] not found: {raw}")
            continue
        clips.append(p)

    if len(clips) < 2:
        fail("Need at least 2 clips.")
        return

    output = _prompt_path("output file", "merged.mp4")
    out = Path(output or "merged.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)

    err.print()
    err.print(Rule(style="muted"))
    err.print()

    ff = get_ffmpeg()
    CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

    with make_progress() as progress:
        task = progress.add_task(f"Merging {len(clips)} clips", total=1)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            concat_file = f.name
            for c in clips:
                f.write(f"file '{str(c.resolve()).replace(chr(92), '/')}'\n")
        try:
            subprocess.run(
                [ff, "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", str(out)],
                capture_output=True, creationflags=CREATE_NO_WINDOW, check=True,
            )
        finally:
            os.unlink(concat_file)
        progress.update(task, completed=1)

    ok(f"{len(clips)} clips → {out}")


def _wizard_info() -> None:
    from .core.video import get_video_info

    err.print()
    err.print(Rule("[accent]info[/]", style="muted"))
    err.print()

    video = _prompt_path("video path", must_exist=True)
    if not video:
        return

    err.print()

    data = get_video_info(video)
    dur = data["duration"]
    h, m, s = int(dur // 3600), int((dur % 3600) // 60), dur % 60
    dur_str = (f"{h}h {m:02d}m {s:05.2f}s" if h else f"{m}m {s:05.2f}s" if m else f"{s:.2f}s")

    console.print(f"[label]{Path(video).name}[/]  [muted]{dur_str}[/]\n")

    def _fmt_br(bps):
        if not bps: return "—"
        return f"{bps/1_000_000:.1f} Mbps" if bps >= 1_000_000 else f"{bps/1_000:.0f} kbps"

    for stream in data["streams"]:
        if stream["type"] == "video":
            t = make_table(("", "muted", {"width": 14}), ("", "label", {}), title="Video")
            t.add_row("Codec", stream["codec"])
            t.add_row("Resolution", f"{stream['width']}×{stream['height']}")
            t.add_row("FPS", str(stream["fps"]))
            t.add_row("Bitrate", _fmt_br(stream["bit_rate"]))
            console.print(t)
        elif stream["type"] == "audio":
            t = make_table(("", "muted", {"width": 14}), ("", "label", {}), title="Audio")
            t.add_row("Codec", stream["codec"])
            t.add_row("Sample rate", f"{stream['sample_rate']} Hz")
            t.add_row("Channels", str(stream["channels"]))
            t.add_row("Bitrate", _fmt_br(stream["bit_rate"]))
            console.print(t)


# ---------------------------------------------------------------------------
# Main session loop
# ---------------------------------------------------------------------------

_COMMANDS = {
    "detect": (_wizard_detect, "split video into scenes"),
    "export": (_wizard_export, "export selected scenes"),
    "merge":  (_wizard_merge,  "merge clips into one file"),
    "info":   (_wizard_info,   "show video metadata"),
}


def run_wizard() -> None:
    """Launch the interactive AMVerge CLI session."""
    os.system("cls" if os.name == "nt" else "clear")

    err.print(f"\n  [accent bold]AMVerge[/] [muted]CLI[/]  [muted]v{__version__}[/]\n")
    err.print(Rule(style="muted"))

    while True:
        err.print()
        parts = "  ·  ".join(
            f"[accent]{cmd}[/]  [muted]{desc}[/]"
            for cmd, (_, desc) in _COMMANDS.items()
        )
        err.print(f"  {parts}")
        err.print(f"  [muted]quit[/]  [muted]exit session[/]")
        err.print()

        raw = _prompt("command", "").lower()

        if raw in ("quit", "exit", "q", ""):
            err.print()
            err.print("  [muted]bye[/]\n")
            break

        if raw not in _COMMANDS:
            err.print(f"  [error]✗[/] unknown command '{raw}'")
            continue

        fn, _ = _COMMANDS[raw]
        try:
            fn()
        except KeyboardInterrupt:
            err.print("\n  [muted]cancelled[/]")

        err.print()
        err.print(Rule(style="muted"))
