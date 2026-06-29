"""TransNetV2 scene cache management.

Usage:
    >>> from amverge import SceneCache
    >>> cache = SceneCache("./cache_dir")
    >>> cache.exists("episode.mp4")
    >>> scenes_secs, scenes_frames = cache.load("episode.mp4")
    >>> cache.save("episode.mp4", scenes_secs, scenes_frames)
    >>> cache.clear("episode.mp4")
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


class SceneCache:
    """Manage TransNetV2 .npy scene detection caches.

    Caches are keyed by a SHA1-based fingerprint of file path, size,
    and modification time. This allows re-opening the same video without
    re-running TransNetV2 detection.

    Args:
        cache_dir: Directory where .npy files are stored.
            Defaults to the current working directory.

    Example:
        >>> cache = SceneCache("./scenes")
        >>> cache.list()
        >>> if not cache.exists("episode.mp4"):
        ...     scenes_secs, scenes_frames = detector.detect_raw("episode.mp4")
        ...     cache.save("episode.mp4", scenes_secs, scenes_frames)
        >>> secs, frm = cache.load("episode.mp4")
    """

    def __init__(self, cache_dir: str | Path = ".") -> None:
        self._dir = Path(cache_dir).resolve()

    @property
    def cache_dir(self) -> Path:
        return self._dir

    def _prefix(self, video_path: str | Path) -> str:
        from ..infra.ipc import build_video_cache_prefix
        return build_video_cache_prefix(Path(video_path))

    def _secs_path(self, video_path: str | Path) -> Path:
        return self._dir / f"{self._prefix(video_path)}_secs.npy"

    def _frames_path(self, video_path: str | Path) -> Path:
        return self._dir / f"{self._prefix(video_path)}_frames.npy"

    def exists(self, video_path: str | Path) -> bool:
        """Check if a cache exists for the given video.

        Args:
            video_path: Path to the source video file.

        Returns:
            True if both ``_secs.npy`` and ``_frames.npy`` files exist.
        """
        return self._secs_path(video_path).exists() and self._frames_path(video_path).exists()

    def list(self) -> dict[str, tuple[str, str]]:
        """List all cached videos with their prefix and file paths.

        Returns:
            Dict mapping cache prefix to ``(secs_path, frames_path)`` tuples.
        """
        result: dict[str, tuple[str, str]] = {}
        for p in sorted(self._dir.glob("*_secs.npy")):
            prefix = p.stem.replace("_secs", "")
            secs = str(p)
            frames = str(self._dir / f"{prefix}_frames.npy")
            result[prefix] = (secs, frames)
        return result

    def load(
        self, video_path: str | Path
    ) -> tuple[np.ndarray, np.ndarray] | None:
        """Load cached scene data for a video.

        Args:
            video_path: Path to the source video file.

        Returns:
            ``(scenes_secs, scenes_frames)`` ndarrays if cache exists,
            or ``None`` if not found.
        """
        secs_p = self._secs_path(video_path)
        frames_p = self._frames_path(video_path)
        if secs_p.exists() and frames_p.exists():
            return np.load(secs_p), np.load(frames_p)
        return None

    def save(
        self,
        video_path: str | Path,
        scenes_secs: np.ndarray,
        scenes_frames: np.ndarray,
    ) -> tuple[str, str]:
        """Save scene data to cache.

        Args:
            video_path: Path to the source video file (for fingerprint).
            scenes_secs: ``(N, 2)`` ndarray of scene boundaries in seconds.
            scenes_frames: ``(N, 2)`` ndarray of scene boundaries in frames.

        Returns:
            ``(secs_path, frames_path)`` tuple of saved file paths.
        """
        secs_p = self._secs_path(video_path)
        frames_p = self._frames_path(video_path)
        self._dir.mkdir(parents=True, exist_ok=True)
        np.save(secs_p, scenes_secs)
        np.save(frames_p, scenes_frames)
        return str(secs_p), str(frames_p)

    def clear(self, video_path: str | Path) -> tuple[str, str] | None:
        """Delete cache files for a specific video.

        Args:
            video_path: Path to the source video file.

        Returns:
            ``(secs_path, frames_path)`` of deleted files, or None if
            no cache existed.
        """
        secs_p = self._secs_path(video_path)
        frames_p = self._frames_path(video_path)
        deleted = []
        for p in (secs_p, frames_p):
            if p.exists():
                p.unlink()
                deleted.append(p)
        if deleted:
            return str(secs_p), str(frames_p)
        return None

    def clear_all(self) -> int:
        """Delete all cache files in the cache directory.

        Returns:
            Number of files deleted.
        """
        count = 0
        for p in self._dir.glob("*_secs.npy"):
            p.unlink()
            count += 1
        for p in self._dir.glob("*_frames.npy"):
            p.unlink()
            count += 1
        return count
