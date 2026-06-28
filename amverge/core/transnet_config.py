"""TransNetV2 model configuration constants and helper.

Usage:
    >>> from amverge import TransNetConfig
    >>> config = TransNetConfig()
    >>> print(config.input_size, config.window_size, config.stride)
"""

from dataclasses import dataclass

from .transnet_constants import (
    FRAME_WIDTH, FRAME_HEIGHT, FRAME_CHANNELS,
    WINDOW_SIZE, OVERLAP, STRIDE,
)


@dataclass(frozen=True)
class TransNetConfig:
    """TransNetV2 model input configuration.

    Attributes:
        input_width: Frame width fed to the model (48).
        input_height: Frame height fed to the model (27).
        input_channels: Color channels (3, RGB).
        input_bytes: Bytes per frame (width * height * channels).
        window_size: Frames per inference batch (100).
        overlap: Overlap between consecutive batches (50).
        stride: Effective step size (window_size - overlap = 50).
        input_size: Tuple of (width, height).
        input_shape: Tuple of (height, width, channels).

    Example:
        >>> config = TransNetConfig()
        >>> print(f"Model input: {config.input_width}x{config.input_height}")
        >>> print(f"Window: {config.window_size} frames, stride: {config.stride}")
        >>> # Calculate frames for a video
        >>> frames = int(24.0 * 120.0)  # 24fps, 120 seconds
        >>> batches = frames // config.stride
        >>> print(f"~{batches} inference batches")
    """

    input_width: int = FRAME_WIDTH
    input_height: int = FRAME_HEIGHT
    input_channels: int = FRAME_CHANNELS
    input_bytes: int = FRAME_WIDTH * FRAME_HEIGHT * FRAME_CHANNELS
    window_size: int = WINDOW_SIZE
    overlap: int = OVERLAP
    stride: int = WINDOW_SIZE - OVERLAP

    @property
    def input_size(self) -> tuple[int, int]:
        return (self.input_width, self.input_height)

    @property
    def input_shape(self) -> tuple[int, int, int]:
        return (self.input_height, self.input_width, self.input_channels)
