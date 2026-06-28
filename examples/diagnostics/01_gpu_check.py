"""GPU and CUDA status check.

Shows PyTorch version, CUDA availability, GPU name and VRAM.
Equivalent to `amverge gpu`.

Usage:
    python 01_gpu_check.py
"""

from amverge import get_gpu_info

info = get_gpu_info()

print(f"PyTorch {info['torch_version'] or 'not installed'}")
if info["torch_version"]:
    print(f"CUDA available: {info['cuda_available']}")
    if info["cuda_available"]:
        print(f"CUDA version:   {info['cuda_version']}")
        print(f"GPU count:      {info['gpu_count']}")
        print(f"GPU:            {info['gpu_name']}  ({info['vram_gb']:.1f} GB VRAM)")
    else:
        print("No CUDA GPU detected. TransNetV2 will use CPU.")
else:
    print("Run: pip install amverge[ml]")

print(f"\nTransNetV2: {'installed' if info['transnetv2_available'] else 'not installed'}")
print(f"OpenCV:     {'installed' if info['opencv_available'] else 'not installed'}")
print(f"DiscordRPC: {'available' if info['rpc_available'] else 'not installed'}")
print(f"Nelux:      {'available' if info['nelux_available'] else 'not found'}")
