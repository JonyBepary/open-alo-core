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
    
    This checks if the portal service is running.
    
    Returns:
        True if portal is available
        
    Example:
        >>> if not is_portal_available():
        ...     print("Portal not available, cannot initialize")
    """
    try:
        import gi
        gi.require_version('Gio', '2.0')
        from gi.repository import Gio
        
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            'org.freedesktop.portal.Desktop',
            '/org/freedesktop/portal/desktop',
            'org.freedesktop.DBus.Introspectable',
            None
        )
        # Try to introspect
        result = proxy.call_sync(
            'Introspect',
            None,
            Gio.DBusCallFlags.NONE,
            1000,
            None
        )
        return result is not None
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
