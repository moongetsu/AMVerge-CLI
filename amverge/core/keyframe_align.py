from __future__ import annotations

from bisect import bisect_left, bisect_right

import av


def get_keyframe_timestamps_pyav(video_path: str) -> list[float]:
    keyframe_times: list[float] = []
    with av.open(video_path) as container:
        stream = container.streams.video[0]
        try:
            stream.discard = type(stream.discard).nonkey
        except (AttributeError, KeyError):
            pass
        for packet in container.demux(stream):
            if not packet.is_keyframe:
                continue
            ts = packet.pts if packet.pts is not None else packet.dts
            if ts is None:
                continue
            keyframe_times.append(round(float(ts * packet.time_base), 2))
    return sorted(set(keyframe_times))


def _nearest_within_threshold(
    sorted_keyframes: list[float], ts: float, threshold: float
) -> tuple[float | None, float | None]:
    i = bisect_left(sorted_keyframes, ts)
    candidates = []
    if i < len(sorted_keyframes):
        candidates.append(sorted_keyframes[i])
    if i > 0:
        candidates.append(sorted_keyframes[i - 1])
    if not candidates:
        return None, None
    nearest = min(candidates, key=lambda k: abs(k - ts))
    diff = abs(nearest - ts)
    if diff <= threshold:
        return nearest, diff
    return None, diff


def classify_scenes_by_keyframe_alignment(
    scenes_secs: list[tuple[float, float]],
    keyframe_timestamps: list[float],
    threshold: float = 0.2,
) -> tuple[list[dict], list[dict]]:
    if threshold < 0:
        raise ValueError(f"Cannot have negative threshold ({threshold})")

    kf = sorted(float(x) for x in keyframe_timestamps)
    copy_candidates: list[dict] = []
    reencode_candidates: list[dict] = []

    for idx, scene in enumerate(scenes_secs):
        scene_start = float(scene[0])
        scene_end = float(scene[1])

        snapped_start, start_diff = _nearest_within_threshold(kf, scene_start, threshold)
        snapped_end, end_diff = _nearest_within_threshold(kf, scene_end, threshold)

        mode = "copy_candidate" if snapped_start is not None else "reencode_candidate"

        record = {
            "scene_id": idx,
            "orig_start": scene_start,
            "orig_end": scene_end,
            "start": snapped_start if snapped_start is not None else scene_start,
            "end": snapped_end if snapped_end is not None else scene_end,
            "start_snapped": snapped_start is not None,
            "end_snapped": snapped_end is not None,
            "start_diff_sec": start_diff,
            "end_diff_sec": end_diff,
            "mode": mode,
        }

        if mode == "copy_candidate":
            copy_candidates.append(record)
        else:
            reencode_candidates.append(record)

    return copy_candidates, reencode_candidates
