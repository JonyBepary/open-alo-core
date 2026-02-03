"""
Simple type definitions for open_alo_core

Using NamedTuple for zero-overhead immutable types.
"""

from typing import NamedTuple


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
        return Point(
            self.x + self.width // 2,
            self.y + self.height // 2
        )
    
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


# Mouse button constants
BUTTON_LEFT = 1
BUTTON_MIDDLE = 2
BUTTON_RIGHT = 3

# Key name normalization
KEY_ALIASES = {
    # Common aliases to standard GTK/GDK names
    'return': 'Return',
    'enter': 'Return',
    'escape': 'Escape',
    'esc': 'Escape',
    'tab': 'Tab',
    'space': 'space',
    'backspace': 'BackSpace',
    'delete': 'Delete',
    'del': 'Delete',
    'home': 'Home',
    'end': 'End',
    'pageup': 'Page_Up',
    'pagedown': 'Page_Down',
    'left': 'Left',
    'right': 'Right',
    'up': 'Up',
    'down': 'Down',
    'ctrl': 'Control',
    'control': 'Control',
    'alt': 'Alt',
    'shift': 'Shift',
    'super': 'Super',
    'win': 'Super',
    'cmd': 'Super',
    'command': 'Super',
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
