"""
Utility functions for open_alo_core
"""

import os
from typing import Literal, Optional


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
        gi.require_version('Gio', '2.0')
        gi.require_version('GLib', '2.0')
        from gi.repository import Gio, GLib

        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        # NameHasOwner: lightweight D-Bus name owner check.
        # Must pass explicit bus name 'org.freedesktop.DBus' as destination
        # (None routes to local bus object which lacks this method).
        result = bus.call_sync(
            'org.freedesktop.DBus',
            '/org/freedesktop/DBus',
            'org.freedesktop.DBus',
            'NameHasOwner',
            GLib.Variant('(s)', ('org.freedesktop.portal.Desktop',)),
            None,
            Gio.DBusCallFlags.NONE,
            500,
            None,
        )
        if result:
            return result.get_child_value(0).get_boolean()
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
        result = subprocess.run(
            ['pw-cli', 'info'],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except Exception:
        return False
