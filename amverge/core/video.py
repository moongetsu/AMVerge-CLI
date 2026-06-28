"""Video metadata helpers."""
from __future__ import annotations

import av


def get_video_duration(path: str) -> float:
    """Get video duration in seconds using PyAV.

    Args:
        path: Path to the video file.

    Returns:
        Duration in seconds as a float.
    """
    with av.open(path) as c:
        return float(c.duration / av.time_base)


def get_video_info(path: str) -> dict:
    """Get full video and audio stream metadata.

    Args:
        path: Path to the video file.

    Returns:
        Dict with keys ``path``, ``duration``, and ``streams``.
        Each stream dict contains ``type``, ``codec``, and type-specific
        fields (``width``, ``height``, ``fps`` for video;
        ``sample_rate``, ``channels`` for audio).
    """
    with av.open(path) as c:
        duration = float(c.duration / av.time_base) if c.duration else 0.0
        info: dict = {"path": path, "duration": duration, "streams": []}

        for stream in c.streams:
            if stream.type == "video":
                fps = float(stream.average_rate) if stream.average_rate else 0.0
                info["streams"].append({
                    "type": "video",
                    "codec": stream.codec_context.name,
                    "width": stream.width,
                    "height": stream.height,
                    "fps": round(fps, 3),
                    "bit_rate": stream.bit_rate,
                })
            elif stream.type == "audio":
                info["streams"].append({
                    "type": "audio",
                    "codec": stream.codec_context.name,
                    "sample_rate": stream.sample_rate,
                    "channels": stream.channels,
                    "bit_rate": stream.bit_rate,
                })

        return info


def merge_short_scenes(boundaries: list[float], min_duration: float = 0.5) -> list[float]:
    """Drop scene boundaries that create scenes shorter than ``min_duration``.

    Args:
        boundaries: Sorted list of timestamps including start and end.
        min_duration: Minimum scene length in seconds (default 0.5).

    Returns:
        Filtered boundary list with short scenes merged.
    """
    if len(boundaries) <= 2:
        return boundaries

    merged = [boundaries[0]]
    for ts in boundaries[1:]:
        if ts - merged[-1] >= min_duration:
            merged.append(ts)

    return merged
