"""
open_alo_core - Standalone Desktop Automation SDK for Linux

Pure hardware abstraction with zero AI/ML dependencies.
Supports Wayland (via XDG Portals).

Version: 0.3.0
"""

__version__ = "0.1.3"

# Public API
__all__ = [
    # Main controllers
    "WaylandInput",
    "WaylandCapture",
    "UnifiedRemoteDesktop",  # Recommended for AI agents
    # Window management
    "WindowManager",
    "WindowInfo",
    "WindowType",
    "FrameType",
    "get_focused_window",
    "find_window",
    "list_windows",
    "activate_window",
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
    "create_unified_desktop",
    "detect_session_type",
    "is_wayland",
    "is_portal_available",
    "is_pipewire_available",
    # Key normalization
    "normalize_key",
]

# Exceptions
from .exceptions import (
    BackendNotAvailable,
    CaptureError,
    CoreError,
    InputError,
    PermissionDenied,
    SessionError,
)

# Types
from .types import (
    BUTTON_LEFT,
    BUTTON_MIDDLE,
    BUTTON_RIGHT,
    Point,
    Rect,
    Size,
    normalize_key,
)

# Utilities
from .utils import (
    detect_session_type,
    is_pipewire_available,
    is_portal_available,
    is_wayland,
)
from .wayland.capture import WaylandCapture

# Core classes
from .wayland.input import WaylandInput
from .wayland.unified import UnifiedRemoteDesktop, create_unified_desktop

# Window management
from .window_manager import (
    FrameType,
    WindowInfo,
    WindowManager,
    WindowType,
    activate_window,
    find_window,
    get_focused_window,
    list_windows,
)
