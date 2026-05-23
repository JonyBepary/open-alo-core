"""
Shared portal helpers for open_alo_core wayland modules.

Provides common utilities used by UnifiedRemoteDesktop, WaylandInput,
and WaylandCapture to reduce code duplication in D-Bus portal interactions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def portal_request(
    bus: Gio.DBusConnection,
    portal: Gio.DBusProxy,
    method: str,
    params: GLib.Variant,
    timeout_seconds: int = 30,
    portal_bus_name: str = "org.freedesktop.portal.Desktop",
) -> Tuple[int, Optional[Dict[str, Any]]]:
    """
    Execute an async portal request and wait for the Response signal.

    Portal D-Bus API uses an asynchronous request pattern:
      1. Call the method → get a request object path
      2. Subscribe to the Response signal on that path
      3. Run a GLib main loop until response or timeout
      4. Return the (error_code, results) tuple

    Args:
        bus: D-Bus session connection
        portal: D-Bus proxy for the portal interface
        method: Method name to call on the portal proxy
        params: GLib.Variant with method parameters
        timeout_seconds: Max seconds to wait for response
        portal_bus_name: D-Bus bus name for signal subscription

    Returns:
        (error_code, results_dict):
            error_code == 0 means success
            results_dict is None if no response within timeout
    """
    from gi.repository import GLib, Gio

    loop = GLib.MainLoop()
    response_data: list = [None, None]  # [error_code, results]

    result = portal.call_sync(
        method,
        params,
        Gio.DBusCallFlags.NONE,
        timeout_seconds * 1000,
        None,
    )

    request_path = result[0]

    def on_response(
        connection, sender: str, path: str, iface: str, signal: str, params_signal
    ) -> None:
        nonlocal response_data
        error_code, results = params_signal
        response_data = [error_code, results]
        loop.quit()

    sub_id = bus.signal_subscribe(
        portal_bus_name,
        "org.freedesktop.portal.Request",
        "Response",
        request_path,
        None,
        Gio.DBusSignalFlags.NONE,
        on_response,
    )

    GLib.timeout_add_seconds(timeout_seconds, loop.quit)
    loop.run()
    bus.signal_unsubscribe(sub_id)

    error_code, results = response_data
    return error_code, results


def char_to_keysym(char: str) -> int:
    """
    Convert a character or key name to an X11 keysym value.

    Handles special key names (Return, Escape, Control, etc.) and
    single Unicode characters.

    Args:
        char: Single character or named key

    Returns:
        X11 keysym integer value (0 for unknown)
    """
    keysym_map = {
        "Return": 0xFF0D,
        "Escape": 0xFF1B,
        "Tab": 0xFF09,
        "BackSpace": 0xFF08,
        "Delete": 0xFFFF,
        "Left": 0xFF51,
        "Up": 0xFF52,
        "Right": 0xFF53,
        "Down": 0xFF54,
        "Control": 0xFFE3,
        "Alt": 0xFFE9,
        "Shift": 0xFFE1,
        "Super": 0xFFEB,
        " ": 0x0020,
    }

    if char in keysym_map:
        return keysym_map[char]

    # For single characters, use Unicode value (valid keysym)
    if len(char) == 1:
        return ord(char)

    return 0
