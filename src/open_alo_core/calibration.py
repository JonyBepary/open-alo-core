"""
Deterministic Coordinate Space Calibration and Solvers
"""

from typing import Optional
from .types import Rect
from .geometry import AffineTransform2D

RESIDUAL_LIMIT_PX = 2.0


def solve_affine(mutter_rect: Rect, atspi_rect: Rect) -> AffineTransform2D:
    """
    Solve full affine transformation (scale + offset) from a matched rect pair:

        scale_x = mutter.width / atspi.width
        scale_y = mutter.height / atspi.height
        offset_x = mutter.x - scale_x * atspi.x
        offset_y = mutter.y - scale_y * atspi.y
    """
    if atspi_rect.width <= 0 or atspi_rect.height <= 0:
        raise ValueError(f"Invalid AT-SPI extents: {atspi_rect}")
    sx = mutter_rect.width / atspi_rect.width
    sy = mutter_rect.height / atspi_rect.height
    ox = mutter_rect.x - sx * atspi_rect.x
    oy = mutter_rect.y - sy * atspi_rect.y
    return AffineTransform2D(sx, sy, ox, oy)


def residual(mutter_rect: Rect, atspi_rect: Rect, t: AffineTransform2D) -> float:
    """
    Compute maximum absolute error in pixels between transformed rect and target rect.
    """
    tr = t.transform_rect(atspi_rect)
    return float(
        max(
            abs(tr.x - mutter_rect.x),
            abs(tr.y - mutter_rect.y),
            abs(tr.width - mutter_rect.width),
            abs(tr.height - mutter_rect.height),
        )
    )
