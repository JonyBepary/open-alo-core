"""
Window Management for Wayland/GNOME

Provides comprehensive window management capabilities via GNOME Shell D-Bus interface.
Requires the Window Calls GNOME extension: https://extensions.gnome.org/extension/4724/window-calls/

This module provides a clean, Pythonic API for window operations including:
- Listing and finding windows
- Window activation and focus
- Window positioning and resizing
- Window state management (maximize, minimize, etc.)
- Workspace management
"""

import json
import subprocess
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Optional, Tuple


class WindowType(IntEnum):
    """Window type enumeration"""

    NORMAL = 0
    DESKTOP = 1
    DOCK = 2
    DIALOG = 3
    MODAL_DIALOG = 4
    TOOLBAR = 5
    MENU = 6
    UTILITY = 7
    SPLASH = 8


class FrameType(IntEnum):
    """Window frame type enumeration"""

    NORMAL = 0
    FRAMELESS = 1


@dataclass
class WindowInfo:
    """Window information container"""

    id: int
    wm_class: str
    wm_class_instance: str
    title: str = ""
    pid: int = 0
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    workspace: int = 0
    monitor: int = 0
    frame_type: int = 0
    window_type: int = 0
    focus: bool = False
    in_current_workspace: bool = False
    maximized: int = 0

    def __repr__(self):
        title_str = self.title if len(self.title) <= 30 else f"{self.title[:27]}..."
        return f"WindowInfo(id={self.id}, wm_class='{self.wm_class}', title='{title_str}', focus={self.focus})"


class WindowManager:
    """
    Window Manager for GNOME Shell via D-Bus

    Provides high-level window management operations using the window-actions extension.
    All methods handle D-Bus communication and parse responses automatically.

    Example:
        >>> wm = WindowManager()
        >>> windows = wm.list_windows()
        >>> editor = wm.find_window("Text Editor")
        >>> wm.activate(editor.id)
        >>> wm.maximize(editor.id)
    """

    DBUS_DEST = "org.gnome.Shell"
    DBUS_PATH = "/org/gnome/Shell/Extensions/Windows"
    DBUS_INTERFACE = "org.gnome.Shell.Extensions.Windows"

    def __init__(self, timeout: int = 5, include_utility: bool = False):
        """
        Initialize WindowManager

        Args:
            timeout: Default timeout for D-Bus calls in seconds
            include_utility: Keep utility/noise windows (Desktop Icons gjs
                layers, XWayland dummy actors with null wm_class). Default
                False filters them from list_windows()/get_window_z_order().
        """
        self.timeout = timeout
        self.include_utility = include_utility
        self.is_available = self._check_extension()

    @staticmethod
    def _is_utility_window(win: "WindowInfo") -> bool:
        """Heuristic for OS noise windows the harness should not see."""
        if not win.wm_class:
            return True  # XWayland dummy actors (null wm_class)
        if win.wm_class == "gjs" and (win.title or "").startswith("Desktop Icons"):
            return True  # desktop icons layer
        return False

    def _check_extension(self) -> bool:
        """Check if Window Calls extension is available"""
        try:
            result = self._dbus_call("List")
            if not result:
                raise RuntimeError(
                    "Window Calls extension not available. "
                    "Install from: https://extensions.gnome.org/extension/4724/window-calls/"
                )
            return True
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(
                "Window Calls extension not available. "
                "Install from: https://extensions.gnome.org/extension/4724/window-calls/"
            ) from e




    def _dbus_call(self, method: str, *args) -> Optional[str]:
        """
        Internal D-Bus call helper

        Args:
            method: Method name to call
            *args: Arguments to pass to the method

        Returns:
            Raw D-Bus response string or None on error
        """
        cmd = [
            "gdbus",
            "call",
            "--session",
            "--dest",
            self.DBUS_DEST,
            "--object-path",
            self.DBUS_PATH,
            "--method",
            f"{self.DBUS_INTERFACE}.{method}",
        ] + [str(arg) for arg in args]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def _parse_json_response(self, response: str) -> any:
        """
        Parse D-Bus JSON response

        D-Bus wraps JSON responses in format: ('[{...}]',)
        This method extracts and parses the actual JSON.
        """
        if not response:
            return None

        # Handle format: ('[...]',) or ('...',)
        if response.startswith("('") and response.endswith("',)"):
            json_str = response[2:-3]  # Remove (' and ',)
            # Unescape unicode sequences
            json_str = json_str.encode().decode("unicode_escape")
            return json.loads(json_str)

        # Fallback: try direct parsing
        try:
            return json.loads(response)
        except:
            return None

    # ==================== Window Listing and Search ====================

    def list_windows(self, current_workspace_only: bool = False) -> List[WindowInfo]:
        """
        List all open windows

        Args:
            current_workspace_only: Only return windows in current workspace

        Returns:
            List of WindowInfo objects

        Example:
            >>> wm = WindowManager()
            >>> for win in wm.list_windows():
            ...     print(f"{win.wm_class}: {win.title}")
        """
        response = self._dbus_call("List")
        if not response:
            return []

        windows_data = self._parse_json_response(response)
        if not windows_data:
            return []

        windows = []
        for data in windows_data:
            if current_workspace_only and not data.get("in_current_workspace", False):
                continue

            windows.append(
                WindowInfo(
                    id=data["id"],
                    wm_class=data.get("wm_class") or "",
                    wm_class_instance=data.get("wm_class_instance") or "",
                    title=data.get("title") or "",
                    pid=data.get("pid", 0),
                    x=data.get("x", 0),
                    y=data.get("y", 0),
                    width=data.get("width", 0),
                    height=data.get("height", 0),
                    workspace=data.get("workspace", 0),
                    monitor=data.get("monitor", 0),
                    frame_type=data.get("frame_type", 0),
                    window_type=data.get("window_type", 0),
                    focus=data.get("focus", False),
                    in_current_workspace=data.get("in_current_workspace", False),
                    maximized=data.get("maximized", 0),
                )
            )

        if not self.include_utility:
            windows = [w for w in windows if not self._is_utility_window(w)]

        return windows

    def find_window(self, query: str, match_title: bool = True) -> Optional[WindowInfo]:
        """
        Find a window by wm_class or title

        Args:
            query: Search string (case-insensitive)
            match_title: Also search in window titles (slower)

        Returns:
            First matching WindowInfo or None

        Example:
            >>> wm = WindowManager()
            >>> editor = wm.find_window("Text Editor")
            >>> if editor:
            ...     wm.activate(editor.id)
        """
        windows = self.list_windows()
        query_lower = query.lower()

        # First try wm_class (fast)
        for window in windows:
            if query_lower in (window.wm_class or "").lower():
                return window

        # Then try titles if enabled
        if match_title:
            for window in windows:
                if query_lower in (window.title or "").lower():
                    return window

        return None

    def find_all_windows(
        self, query: str, match_title: bool = True
    ) -> List[WindowInfo]:
        """
        Find all windows matching query

        Args:
            query: Search string (case-insensitive)
            match_title: Also search in window titles

        Returns:
            List of matching WindowInfo objects
        """
        windows = self.list_windows()
        query_lower = query.lower()
        matches = []

        for window in windows:
            if query_lower in (window.wm_class or "").lower() or (
                match_title and query_lower in (window.title or "").lower()
            ):
                matches.append(window)

        return matches

    def get_window_z_order(self) -> List[int]:
        """
        Get all window IDs in visual stacking order from bottom to top.

        The last ID in the returned list is the top-most (front-most) window.

        Returns:
            List of window IDs in stacking order (bottom to top).

        Example:
            >>> wm = WindowManager()
            >>> z_order = wm.get_window_z_order()
            >>> top_win_id = z_order[-1] if z_order else None
        """
        response = self._dbus_call("GetWindowZOrder")
        if response:
            data = self._parse_json_response(response)
            if isinstance(data, list):
                ids = [int(x) for x in data if isinstance(x, (int, float))]
                if not self.include_utility:
                    utility_ids = set()
                    raw = self._dbus_call("List")
                    parsed = self._parse_json_response(raw) if raw else None
                    for d in parsed or []:
                        if not isinstance(d, dict):
                            continue
                        probe = WindowInfo(
                            id=d.get("id", 0),
                            wm_class=d.get("wm_class") or "",
                            wm_class_instance=d.get("wm_class_instance") or "",
                            title=d.get("title") or "",
                        )
                        if self._is_utility_window(probe):
                            utility_ids.add(probe.id)
                    if utility_ids:
                        ids = [i for i in ids if i not in utility_ids]
                return ids

        # Fallback to list_windows() order (which enumerates window actors bottom-to-top)
        windows = self.list_windows()
        return [win.id for win in windows]

    def wait_for_window(
        self,
        query: str,
        match_title: bool = True,
        timeout: float = 5.0,
        poll_interval: float = 0.05,
    ) -> Optional[WindowInfo]:
        """
        Poll until a window matching query appears or timeout expires.

        Args:
            query: Search string for wm_class or title.
            match_title: Whether to match on title as well.
            timeout: Max seconds to wait.
            poll_interval: Delay between checks (seconds).

        Returns:
            Matching WindowInfo if found, or None if timed out.

        Example:
            >>> wm = WindowManager()
            >>> win = wm.wait_for_window("Brave", timeout=3.0)
        """
        import time

        start = time.monotonic()
        while time.monotonic() - start < timeout:
            win = self.find_window(query, match_title=match_title)
            if win:
                return win
            time.sleep(poll_interval)
        return None

    def get_focused_window(self) -> Optional[WindowInfo]:
        """
        Get currently focused window

        Returns:
            WindowInfo of focused window or None
        """
        windows = self.list_windows()
        for window in windows:
            if window.focus:
                return window
        return None

    def get_details(self, window_id: int) -> Optional[Dict]:
        """
        Get detailed information about a window

        Args:
            window_id: Window ID

        Returns:
            Dictionary with detailed window properties
        """
        response = self._dbus_call("Details", window_id)
        if not response:
            return None
        return self._parse_json_response(response)

    def get_title(self, window_id: int) -> Optional[str]:
        """
        Get window title by ID

        Args:
            window_id: Window ID

        Returns:
            Window title string or None
        """
        response = self._dbus_call("GetTitle", window_id)
        if not response:
            return None
        # Response format: ('title',) or ('"title"',)
        if response.startswith("('") and response.endswith("',)"):
            inner = response[2:-3]
            if inner.startswith('"') and inner.endswith('"'):
                try:
                    return json.loads(inner)
                except Exception:
                    pass
            return inner
        try:
            parsed = self._parse_json_response(response)
            if isinstance(parsed, str):
                return parsed
        except Exception:
            pass
        return None



    # ==================== Window State Management ====================

    def activate(self, window_id: int) -> bool:
        """
        Activate (focus) a window

        Args:
            window_id: Window ID

        Returns:
            True if successful
        """
        response = self._dbus_call("Activate", window_id)
        return response is not None

    def maximize(self, window_id: int) -> bool:
        """Maximize a window"""
        response = self._dbus_call("Maximize", window_id)
        return response is not None

    def unmaximize(self, window_id: int) -> bool:
        """Unmaximize a window"""
        response = self._dbus_call("Unmaximize", window_id)
        return response is not None

    def minimize(self, window_id: int) -> bool:
        """Minimize a window"""
        response = self._dbus_call("Minimize", window_id)
        return response is not None

    def unminimize(self, window_id: int) -> bool:
        """Unminimize (restore) a window"""
        response = self._dbus_call("Unminimize", window_id)
        return response is not None

    def close(self, window_id: int) -> bool:
        """Close a window"""
        response = self._dbus_call("Close", window_id)
        return response is not None

    def make_fullscreen(self, window_id: int) -> bool:
        """
        Make a window fullscreen.

        Args:
            window_id: Window ID

        Returns:
            True if successful

        Example:
            >>> wm = WindowManager()
            >>> wm.make_fullscreen(window.id)
        """
        response = self._dbus_call("MakeFullscreen", window_id)
        return response is not None

    def unmake_fullscreen(self, window_id: int) -> bool:
        """
        Exit fullscreen for a window.

        Args:
            window_id: Window ID

        Returns:
            True if successful

        Example:
            >>> wm = WindowManager()
            >>> wm.unmake_fullscreen(window.id)
        """
        response = self._dbus_call("UnmakeFullscreen", window_id)
        return response is not None

    def toggle_fullscreen(self, window_id: int) -> bool:
        """
        Toggle fullscreen state of a window.

        If the window is currently fullscreen, exits fullscreen.
        If not, makes it fullscreen.

        Args:
            window_id: Window ID

        Returns:
            True if successful

        Example:
            >>> wm = WindowManager()
            >>> wm.toggle_fullscreen(window.id)
        """
        details = self.get_details(window_id)
        if details and details.get("fullscreen", False):
            return self.unmake_fullscreen(window_id)
        return self.make_fullscreen(window_id)


    # ==================== Window Positioning ====================

    def move(self, window_id: int, x: int, y: int) -> bool:
        """
        Move window to position

        Args:
            window_id: Window ID
            x: X coordinate (can be negative)
            y: Y coordinate (can be negative)

        Returns:
            True if successful
        """
        response = self._dbus_call("Move", window_id, x, y)
        return response is not None

    def resize(self, window_id: int, width: int, height: int) -> bool:
        """
        Resize window

        Args:
            window_id: Window ID
            width: New width in pixels
            height: New height in pixels

        Returns:
            True if successful
        """
        response = self._dbus_call("Resize", window_id, width, height)
        return response is not None

    def move_resize(
        self, window_id: int, x: int, y: int, width: int, height: int
    ) -> bool:
        """
        Move and resize window in one operation

        Args:
            window_id: Window ID
            x: X coordinate
            y: Y coordinate
            width: Width in pixels
            height: Height in pixels

        Returns:
            True if successful
        """
        response = self._dbus_call("MoveResize", window_id, x, y, width, height)
        return response is not None

    def get_frame_rect(self, window_id: int) -> Optional[Dict]:
        """
        Get window frame rectangle

        Args:
            window_id: Window ID

        Returns:
            Dictionary with x, y, width, height or None
        """
        response = self._dbus_call("GetFrameRect", window_id)
        if not response:
            return None
        return self._parse_json_response(response)

    def get_frame_bounds(self, window_id: int) -> Optional[Dict]:
        """
        Get window frame bounds

        Args:
            window_id: Window ID

        Returns:
            Dictionary with frame bounds or None
        """
        response = self._dbus_call("GetFrameBounds", window_id)
        if not response:
            return None
        return self._parse_json_response(response)

    # ==================== Workspace Management ====================

    def move_to_workspace(self, window_id: int, workspace_num: int) -> bool:
        """
        Move window to different workspace

        Args:
            window_id: Window ID
            workspace_num: Target workspace number (0-indexed)

        Returns:
            True if successful
        """
        response = self._dbus_call("MoveToWorkspace", window_id, workspace_num)
        return response is not None


# ==================== Convenience Functions ====================


def list_windows(current_workspace_only: bool = False) -> List[WindowInfo]:
    """Convenience function to list windows"""
    wm = WindowManager()
    return wm.list_windows(current_workspace_only)


def find_window(query: str, match_title: bool = True) -> Optional[WindowInfo]:
    """Convenience function to find a window"""
    wm = WindowManager()
    return wm.find_window(query, match_title)


def activate_window(query_or_id, **kwargs) -> bool:
    """
    Convenience function to activate a window

    Args:
        query_or_id: Window ID (int) or search query (str)
        **kwargs: Additional args for find_window if query is str

    Returns:
        True if window was activated

    Example:
        >>> activate_window("Text Editor")
        >>> activate_window(1290274482)
    """
    wm = WindowManager()

    if isinstance(query_or_id, int):
        return wm.activate(query_or_id)
    else:
        window = wm.find_window(query_or_id, **kwargs)
        if window:
            return wm.activate(window.id)
        return False


def get_focused_window() -> Optional[WindowInfo]:
    """Convenience function to get focused window"""
    wm = WindowManager()
    return wm.get_focused_window()


def get_window_z_order() -> List[int]:
    """Convenience function to get window Z-order (stacking order bottom-to-top)"""
    wm = WindowManager()
    return wm.get_window_z_order()


def wait_for_window(
    query: str, match_title: bool = True, timeout: float = 5.0, poll_interval: float = 0.05
) -> Optional[WindowInfo]:
    """Convenience function to wait for a window to appear"""
    wm = WindowManager()
    return wm.wait_for_window(query, match_title=match_title, timeout=timeout, poll_interval=poll_interval)

