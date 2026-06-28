"""Image crop, rotate, and flip utility.

Usage:
    >>> from amverge import ImageCrop
    >>> crop = ImageCrop(x=10, y=10, width=200, height=200, rotation=90)
    >>> crop.apply("input.jpg", "output.jpg")
    >>> crop.apply("animated.gif", "output.gif")
"""

from __future__ import annotations

from pathlib import Path

from .image import CropData, crop_image


class ImageCrop(CropData):
    """Crop rectangle with rotation, flips, and an apply method.

    Inherits from :class:`CropData`. Adds :meth:`apply` for convenience.

    Args:
        x: Left offset in pixels.
        y: Top offset in pixels.
        width: Crop width in pixels.
        height: Crop height in pixels.
        rotation: Rotation angle in degrees (default 0).
        flip_h: Horizontal flip (default False).
        flip_v: Vertical flip (default False).

    Example:
        >>> crop = ImageCrop(x=10, y=10, width=200, height=200, rotation=90)
        >>> crop.apply("input.jpg", "output.jpg")
        >>>
        >>> crop = ImageCrop.from_dict({"x": 10, "y": 10, "width": 200, "height": 200})
        >>> crop.flip_h = True
        >>> crop.apply("image.png", "flipped.png")
    """

    def apply(self, source: str | Path, dest: str | Path) -> str:
        """Apply crop/rotate/flip to an image and save.

        Supports JPEG, PNG, WebP, and animated GIF.

        Args:
            source: Path to the source image file.
            dest: Path for the output image file.

        Returns:
            The output path.
        """
        dest_path = str(Path(dest).resolve())
        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
        crop_image(str(source), dest_path, self)
        return dest_path
