"""
open_alo_core - Standalone Desktop Automation SDK for Linux

Pure hardware abstraction with zero AI/ML dependencies.
Supports Wayland (via XDG Portals).

Version: 0.1.0 (Wayland MVP)
"""

__version__ = "0.1.0"

# Public API
__all__ = [
    # Main controllers
    "WaylandInput",
    "WaylandCapture",
    "UnifiedRemoteDesktop",  # Recommended for AI agents
    "find_window",

    # Window management (new)
    "WindowManager",
    "WindowInfo",
    "WindowType",
    "FrameType",
    "get_focused_window",

    # Types
    "Point",
    "Size",
    "Rect",

    # Constants
    "BUTTON_LEFT",
    "BUTTON_MIDDLE",
    "BUTTON_RIGHT",

    # Exceptions
    "CoreError",
    "PermissionDenied",
    "CaptureError",
    "InputError",
    "SessionError",
    "BackendNotAvailable",

    # Utilities
    "detect_session_type",
    "is_wayland",
    "is_portal_available",
    "is_pipewire_available",

    # Key normalization
    "normalize_key",
]

# Core classes
from .wayland.input import WaylandInput
from .wayland.capture import WaylandCapture
from .wayland.unified import UnifiedRemoteDesktop

# Window management (legacy from old window.py)
from .window import activate_window as _old_activate_window
from .window import list_windows as _old_list_windows
from .window import find_window as _old_find_window

# Window management (new comprehensive API)
from .window_manager import (
    WindowManager,
    WindowInfo,
    WindowType,
    FrameType,
    list_windows,
    find_window,
    activate_window,
    get_focused_window,
)

# Types
from .types import Point, Size, Rect, BUTTON_LEFT, BUTTON_MIDDLE, BUTTON_RIGHT, normalize_key

# Exceptions
from .exceptions import (
    CoreError,
    PermissionDenied,
    CaptureError,
    InputError,
    SessionError,
    BackendNotAvailable,
)

# Utilities
from .utils import detect_session_type, is_wayland, is_portal_available, is_pipewire_available
