"""
Pure Geometric Preflight Verification

Provides low-level coordinate bounds, sentinel value validation, and
z-order window occlusion checks with zero dependencies on AST, semantic nodes,
or action grammar.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .types import Point, Rect
from .utils import sanitize_rect


@dataclass(frozen=True)
class GeometricPreflightVerdict:
    """Result of geometric preflight verification"""

    is_safe: bool
    reason: str


class GeometricPreflight:
    """
    Substrate preflight validator for coordinate boundaries and window stacking.
    """

    def __init__(self, stream_size: Tuple[int, int] = (1920, 1080)):
        self.stream_size = stream_size

    def verify_point_bounds(
        self,
        pt: Point,
        stream_size: Optional[Tuple[int, int]] = None,
    ) -> GeometricPreflightVerdict:
        """
        Validate that a point is within valid positive screen coordinates
        and not an uninitialized or sentinel value.
        """
        sz = stream_size or self.stream_size
        sanitized = sanitize_rect(Rect(pt.x, pt.y, 2, 2), screen_size=sz)
        if sanitized is None:
            return GeometricPreflightVerdict(
                is_safe=False,
                reason=f"Target coordinate {pt} failed sentinel/bounds validation for screen size {sz}",
            )
        return GeometricPreflightVerdict(is_safe=True, reason="Point is within stream bounds")

    def verify_point_occlusion(
        self,
        pt: Point,
        win_id: int,
        window_rects: Dict[int, Rect],
        z_order: List[int],
    ) -> GeometricPreflightVerdict:
        """
        Check if a target point on a given window is covered/occluded by any
        window higher in the desktop z-order.
        """
        if not z_order or win_id not in z_order:
            return GeometricPreflightVerdict(is_safe=True, reason="Window not in z-order")

        win_idx = z_order.index(win_id)
        for higher_id in z_order[win_idx + 1 :]:
            higher_rect = window_rects.get(higher_id)
            if higher_rect and higher_rect.contains(pt):
                return GeometricPreflightVerdict(
                    is_safe=False,
                    reason=f"Target coordinate {pt} on win_id={win_id} is occluded by higher window win_id={higher_id}",
                )

        return GeometricPreflightVerdict(is_safe=True, reason="Point is not occluded")

    def is_point_occluded(
        self,
        pt: Point,
        win_id: int,
        window_rects: Dict[int, Rect],
        z_order: List[int],
    ) -> bool:
        """Convenience boolean check for point occlusion"""
        return not self.verify_point_occlusion(pt, win_id, window_rects, z_order).is_safe
