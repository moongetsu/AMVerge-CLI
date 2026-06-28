"""Diagnostic helpers for GPU, dependencies, and environment checks.

Usage:
    >>> from amverge import get_gpu_info, get_versions
    >>> info = get_gpu_info()
    >>> print(info["gpu_name"])
"""

from __future__ import annotations


def get_gpu_info() -> dict:
    """Get GPU and CUDA information.

    Returns a dict with keys:
        torch_version, cuda_available, cuda_version, gpu_count,
        gpu_name, vram_gb, transnetv2_available, opencv_available,
        rpc_available, nelux_available.

    Example:
        >>> info = get_gpu_info()
        >>> if info["cuda_available"]:
        ...     print(f"GPU: {info['gpu_name']} ({info['vram_gb']:.1f} GB)")
    """
    info: dict = {
        "torch_version": None,
        "cuda_available": False,
        "cuda_version": None,
        "gpu_count": 0,
        "gpu_name": None,
        "vram_gb": 0.0,
        "transnetv2_available": False,
        "opencv_available": False,
        "rpc_available": False,
        "nelux_available": False,
    }

    try:
        import torch
        info["torch_version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["cuda_version"] = torch.version.cuda
            info["gpu_count"] = torch.cuda.device_count()
            if torch.cuda.device_count() > 0:
                info["gpu_name"] = torch.cuda.get_device_name(0)
                props = torch.cuda.get_device_properties(0)
                info["vram_gb"] = props.total_memory / (1024 ** 3)
    except ImportError:
        pass

    try:
        from .scene_detection import TRANSNET_AVAILABLE
        info["transnetv2_available"] = TRANSNET_AVAILABLE
    except ImportError:
        pass

    try:
        import cv2
        info["opencv_available"] = True
    except ImportError:
        pass

    try:
        from .discord_rpc import RPC_AVAILABLE
        info["rpc_available"] = RPC_AVAILABLE
    except ImportError:
        pass

    try:
        from .nelux_runtime import _get_nelux_video_reader
        _get_nelux_video_reader()
        info["nelux_available"] = True
    except (ImportError, Exception):
        pass

    return info


def get_versions() -> dict:
    """Get version info for all dependencies.

    Returns a dict with keys matching package names.

    Example:
        >>> versions = get_versions()
        >>> print(f"amverge {versions['amverge']}")
    """
    from ..__version__ import __version__
    versions: dict = {"amverge": __version__}

    for name in ["av", "numpy", "pillow", "rich", "typer", "tqdm"]:
        try:
            mod = __import__(name)
            versions[name] = getattr(mod, "__version__", "installed")
        except ImportError:
            versions[name] = None

    optional = ["torch", "transnetv2_pytorch", "cv2", "pypresence"]
    for name in optional:
        try:
            mod = __import__(name)
            versions[name] = getattr(mod, "__version__", "installed")
        except ImportError:
            versions[name] = None

    return versions
