"""
open_alo_core - Standalone Desktop Automation SDK for Linux

Pure hardware abstraction with zero AI/ML dependencies.
Supports Wayland (via XDG Portals).

Version: 0.3.0
"""

__version__ = "0.3.0"


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
    "get_window_z_order",
    "find_window",
    "list_windows",
    "activate_window",
    "wait_for_window",
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
    "get_monotonic_ns",
    "sanitize_rect",
    "map_global_to_stream",
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
    get_monotonic_ns,
    is_pipewire_available,
    is_portal_available,
    is_wayland,
    map_global_to_stream,
    sanitize_rect,
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
    get_window_z_order,
    list_windows,
    wait_for_window,
)

