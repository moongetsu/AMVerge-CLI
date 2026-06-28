"""HEVC codec detection via ffprobe. (V1 API - delegates to codec_utils.)"""
from __future__ import annotations

from .codec_utils import check_if_hevc


def is_hevc(video_path: str) -> bool:
    """Return True if the first video stream is encoded as HEVC/H.265.

    Delegates to :func:`~amverge.core.codec_utils.check_if_hevc`.
    """
    return check_if_hevc(video_path)
