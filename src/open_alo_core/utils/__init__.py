"""
Utility functions for open_alo_core
"""

import os
from typing import Any, Dict, Literal, Optional, Tuple

from ..types import Point, Rect, Size


def detect_session_type() -> Literal["wayland", "x11", "unknown"]:
    """
    Detect if running in Wayland or X11 session.

    Returns:
        "wayland" - Running on Wayland
        "x11" - Running on X11
        "unknown" - Cannot determine

    Example:
        >>> session = detect_session_type()
        >>> if session == "wayland":
        ...     print("Using Wayland backend")
    """
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    elif os.environ.get("DISPLAY"):
        return "x11"
    else:
        return "unknown"


def is_wayland() -> bool:
    """
    Check if running on Wayland.

    Returns:
        True if WAYLAND_DISPLAY is set

    Example:
        >>> if is_wayland():
        ...     ctrl = WaylandInput()
        ... else:
        ...     raise RuntimeError("Wayland required")
    """
    return os.environ.get("WAYLAND_DISPLAY") is not None


def is_portal_available() -> bool:
    """
    Check if XDG Desktop Portal is available.

    Uses a lightweight D-Bus name owner check instead of a full
    introspection call for faster response.

    Returns:
        True if portal is available
    """
    try:
        import gi

        gi.require_version("Gio", "2.0")
        gi.require_version("GLib", "2.0")
        from gi.repository import Gio, GLib

        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        # NameHasOwner: lightweight D-Bus name owner check.
        # Must pass explicit bus name 'org.freedesktop.DBus' as destination
        # (None routes to local bus object which lacks this method).
        result = bus.call_sync(
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus",
            "NameHasOwner",
            GLib.Variant("(s)", ("org.freedesktop.portal.Desktop",)),
            None,
            Gio.DBusCallFlags.NONE,
            500,
            None,
        )
        if result:
            return bool(result.get_child_value(0).get_boolean())
        return False
    except Exception:
        return False


def is_pipewire_available() -> bool:
    """
    Check if PipeWire is available for screen capture.

    Returns:
        True if PipeWire is running
    """
    try:
        import subprocess

        result = subprocess.run(["pw-cli", "info"], capture_output=True, timeout=2)
        return result.returncode == 0
    except Exception:
        return False


def get_monotonic_ns() -> int:
    """
    Get current monotonic timestamp in nanoseconds.

    Uses GLib.get_monotonic_time() * 1000 (microseconds to nanoseconds)
    if available, falling back to time.monotonic_ns().

    Returns:
        Monotonic timestamp in nanoseconds.
    """
    try:
        import gi

        gi.require_version("GLib", "2.0")
        from gi.repository import GLib

        return int(GLib.get_monotonic_time() * 1000)
    except Exception:
        import time

        return time.monotonic_ns()


def sanitize_rect(
    rect: Rect,
    screen_size: Optional[Tuple[int, int]] = None,
) -> Optional[Rect]:
    """
    Sanitize and clamp bounding rectangle.

    Filters out:
    - Sentinel values (-2147483648 / INT_MIN)
    - Zero or non-positive dimensions (w <= 1 or h <= 1)
    - Non-visible / out-of-screen bounds (when screen_size is provided)

    Args:
        rect: Raw Rect from AT-SPI / OS.
        screen_size: Optional (width, height) to clamp bounds.

    Returns:
        Sanitized Rect clamped to screen bounds, or None if invalid/offscreen.

    Example:
        >>> sanitize_rect(Rect(-2147483648, -2147483648, 1, 1))
        None
        >>> sanitize_rect(Rect(10, 20, 100, 50), screen_size=(1920, 1080))
        Rect(10, 20, 100, 50)
    """
    INT_MIN_SENTINEL = -2147483648
    if rect.x == INT_MIN_SENTINEL or rect.y == INT_MIN_SENTINEL:
        return None
    if rect.width <= 1 or rect.height <= 1:
        return None

    if screen_size is not None:
        sw, sh = screen_size
        if sw <= 0 or sh <= 0:
            return None
        # Out of bounds completely
        if rect.x + rect.width <= 0 or rect.y + rect.height <= 0:
            return None
        if rect.x >= sw or rect.y >= sh:
            return None

        # Clamp
        nx = max(0, rect.x)
        ny = max(0, rect.y)
        nw = min(sw - nx, rect.width - (nx - rect.x))
        nh = min(sh - ny, rect.height - (ny - rect.y))
        if nw <= 1 or nh <= 1:
            return None
        return Rect(nx, ny, nw, nh)

    return rect


def map_global_to_stream(
    point: Point,
    stream_info: Dict[str, Any],
) -> Point:
    """
    Transform global workspace coordinates to stream-relative coordinates.

    Subtracts the stream position offset from global coordinates.

    Args:
        point: Point in global screen space.
        stream_info: Stream metadata dict from get_stream_info().

    Returns:
        Point in stream coordinate space.

    Example:
        >>> stream = {"position": (1432, 0), "size": (1854, 1048)}
        >>> map_global_to_stream(Point(1500, 100), stream)
        Point(68, 100)
    """
    pos = stream_info.get("position") if isinstance(stream_info, dict) else None
    if pos is None:
        pos = (0, 0)
    return Point(point.x - pos[0], point.y - pos[1])


