"""
2D Geometry and Affine Coordinate Transformations
"""

from dataclasses import dataclass
from .types import Point, Rect


@dataclass(frozen=True)
class AffineTransform2D:
    """
    Represents a 2D affine mapping between coordinate spaces (e.g. AT-SPI vs Mutter/OS screen):

        x_global = scale_x * x_local + offset_x
        y_global = scale_y * y_local + offset_y
    """

    scale_x: float = 1.0
    scale_y: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0

    def transform_point(self, pt: Point) -> Point:
        """Transform point to target coordinate space"""
        gx = int(round(self.scale_x * pt.x + self.offset_x))
        gy = int(round(self.scale_y * pt.y + self.offset_y))
        return Point(gx, gy)

    def transform_rect(self, rect: Rect) -> Rect:
        """Transform bounding box to target coordinate space"""
        gx = int(round(self.scale_x * rect.x + self.offset_x))
        gy = int(round(self.scale_y * rect.y + self.offset_y))
        gw = max(1, int(round(self.scale_x * rect.width)))
        gh = max(1, int(round(self.scale_y * rect.height)))
        return Rect(gx, gy, gw, gh)

    def inverse_point(self, pt: Point) -> Point:
        """Transform target coordinate point back to source space"""
        if self.scale_x == 0 or self.scale_y == 0:
            raise ValueError("Cannot invert affine transform with zero scale")
        ax = int(round((pt.x - self.offset_x) / self.scale_x))
        ay = int(round((pt.y - self.offset_y) / self.scale_y))
        return Point(ax, ay)

    def inverse_rect(self, rect: Rect) -> Rect:
        """Transform target bounding box back to source space"""
        if self.scale_x == 0 or self.scale_y == 0:
            raise ValueError("Cannot invert affine transform with zero scale")
        ax = int(round((rect.x - self.offset_x) / self.scale_x))
        ay = int(round((rect.y - self.offset_y) / self.scale_y))
        aw = max(1, int(round(rect.width / self.scale_x)))
        ah = max(1, int(round(rect.height / self.scale_y)))
        return Rect(ax, ay, aw, ah)
