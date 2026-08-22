"""
Simple type definitions for open_alo_core

Using NamedTuple for zero-overhead immutable types.
"""

from dataclasses import dataclass
from typing import Any, Dict, NamedTuple, Optional, Tuple


class Point(NamedTuple):
    """2D screen coordinates"""

    x: int
    y: int

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"


class Size(NamedTuple):
    """Width and height dimensions"""

    width: int
    height: int

    def __repr__(self) -> str:
        return f"Size({self.width}, {self.height})"


class Rect(NamedTuple):
    """Rectangle with position and size"""

    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> Point:
        """Center point of rectangle"""
        return Point(self.x + self.width // 2, self.y + self.height // 2)

    @property
    def top_left(self) -> Point:
        """Top-left corner"""
        return Point(self.x, self.y)

    @property
    def bottom_right(self) -> Point:
        """Bottom-right corner"""
        return Point(self.x + self.width, self.y + self.height)

    def contains(self, point: Point) -> bool:
        """Check if point is inside rectangle"""
        return (
            self.x <= point.x <= self.x + self.width
            and self.y <= point.y <= self.y + self.height
        )

    def __repr__(self) -> str:
        return f"Rect({self.x}, {self.y}, {self.width}, {self.height})"


@dataclass(frozen=True)
class StreamGeometry:
    """
    Metadata and geometric boundaries for an active Wayland ScreenCast stream.
    """

    position: Tuple[int, int] = (0, 0)
    size: Tuple[int, int] = (1920, 1080)
    logical_size: Tuple[int, int] = (1920, 1080)
    scale: float = 1.0
    node_id: Optional[int] = None
    source_type: Optional[int] = None

    @property
    def rect(self) -> Rect:
        """Global stream rectangle in compositor coordinate space"""
        return Rect(self.position[0], self.position[1], self.size[0], self.size[1])

    @property
    def width(self) -> int:
        return self.size[0]

    @property
    def height(self) -> int:
        return self.size[1]

    def is_in_stream(self, rect: Rect) -> bool:
        """Check if bounding box intersects with the active stream viewport"""
        if rect.width <= 1 or rect.height <= 1:
            return False
        if rect.x + rect.width <= self.position[0]:
            return False
        if rect.x >= self.position[0] + self.size[0]:
            return False
        if rect.y + rect.height <= self.position[1]:
            return False
        if rect.y >= self.position[1] + self.size[1]:
            return False
        return True

    def clamp_to_stream(self, rect: Rect) -> Optional[Rect]:
        """
        Clamp bounding box to active stream viewport boundaries.
        Returns None if out of bounds or dimensions <= 1.
        """
        clamped_x = max(self.position[0], min(rect.x, self.position[0] + self.size[0]))
        clamped_y = max(self.position[1], min(rect.y, self.position[1] + self.size[1]))
        max_r = min(self.position[0] + self.size[0], rect.x + rect.width)
        max_b = min(self.position[1] + self.size[1], rect.y + rect.height)
        clamped_w = max_r - clamped_x
        clamped_h = max_b - clamped_y
        if clamped_w <= 1 or clamped_h <= 1:
            return None
        return Rect(clamped_x, clamped_y, clamped_w, clamped_h)

    def stream_to_global_point(self, pt: Point) -> Point:
        """Map stream-relative coordinates to global compositor coordinates"""
        return Point(pt.x + self.position[0], pt.y + self.position[1])

    def global_to_stream_point(self, pt: Point) -> Point:
        """Map global compositor coordinates to stream-relative coordinates"""
        return Point(pt.x - self.position[0], pt.y - self.position[1])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "position": self.position,
            "size": self.size,
            "logical_size": self.logical_size,
            "scale": self.scale,
            "node_id": self.node_id,
            "source_type": self.source_type,
        }

    def __getitem__(self, key: str) -> Any:
        """Dict-like indexing for backward compatibility"""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get for backward compatibility"""
        return getattr(self, key, default)


# Mouse button constants
BUTTON_LEFT = 1
BUTTON_MIDDLE = 2
BUTTON_RIGHT = 3

# Key name normalization
KEY_ALIASES = {
    # Common aliases to standard GTK/GDK names
    "return": "Return",
    "enter": "Return",
    "escape": "Escape",
    "esc": "Escape",
    "tab": "Tab",
    "space": "space",
    "backspace": "BackSpace",
    "delete": "Delete",
    "del": "Delete",
    "home": "Home",
    "end": "End",
    "pageup": "Page_Up",
    "pagedown": "Page_Down",
    "left": "Left",
    "right": "Right",
    "up": "Up",
    "down": "Down",
    "ctrl": "Control",
    "control": "Control",
    "alt": "Alt",
    "shift": "Shift",
    "super": "Super",
    "win": "Super",
    "cmd": "Super",
    "command": "Super",
}


def normalize_key(key: str) -> str:
    """
    Normalize key name to standard form.

    Examples:
        >>> normalize_key("enter")
        'Return'
        >>> normalize_key("ctrl")
        'Control'
        >>> normalize_key("Return")  # Already normalized
        'Return'
    """
    return KEY_ALIASES.get(key.lower(), key)
