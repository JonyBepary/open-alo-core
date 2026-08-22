"""
Wayland input controller using XDG RemoteDesktop Portal

Provides mouse and keyboard control on Wayland without root privileges.
Uses persistent permissions so user only approves once.

Note: This is the LEGACY module. New code should use UnifiedRemoteDesktop
instead, which provides both input AND capture through a single permission dialog.
"""

import json
import time
import uuid
from pathlib import Path
from typing import List, Optional

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")

from gi.repository import Gio, GLib

from ..exceptions import InputError, PermissionDenied, SessionError
from ..types import Point, normalize_key
from ._portal_helpers import char_to_keysym, portal_request

# Linux evdev button codes - see unified.py EVDEV_BUTTON_MAP note.
EVDEV_BUTTON_MAP = {
    1: 0x110,  # BTN_LEFT
    2: 0x112,  # BTN_MIDDLE
    3: 0x111,  # BTN_RIGHT
}


class WaylandInput:
    """
    Wayland input controller using XDG RemoteDesktop Portal

    Features:
    - Mouse movement, clicking, dragging
    - Keyboard typing, key presses, combinations
    - Persistent permission tokens (persist_mode=2)
    - Clean resource management

    Example:
        >>> with WaylandInput() as ctrl:
        ...     ctrl.initialize(persist_mode=2)
        ...     ctrl.click(Point(500, 500))
        ...     ctrl.type_text("Hello World")

    Args:
        token_path: Custom path for storing restore tokens.
                   If None, uses ~/.config/open_alo_core/tokens.json
    """

    PORTAL_BUS = "org.freedesktop.portal.Desktop"
    PORTAL_PATH = "/org/freedesktop/portal/desktop"
    PORTAL_IFACE = "org.freedesktop.portal.RemoteDesktop"

    def __init__(self, token_path: Optional[Path] = None):
        """
        Initialize input controller

        Args:
            token_path: Path to store permission tokens.
                       None = no persistence (ephemeral session)
        """
        self._session_handle: Optional[str] = None
        self._initialized = False

        # Token storage
        if token_path is None:
            token_path = Path.home() / ".config" / "open_alo_core" / "tokens.json"
        self._token_path = Path(token_path)

        # D-Bus connection (lazy initialization)
        self._bus: Optional[Gio.DBusConnection] = None
        self._portal: Optional[Gio.DBusProxy] = None

    def __enter__(self) -> "WaylandInput":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - auto cleanup"""
        self.close()
        return False

    def _ensure_dbus(self) -> None:
        """Lazy initialization of D-Bus connection"""
        if self._bus is not None:
            return

        self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self._portal = Gio.DBusProxy.new_sync(
            self._bus,
            Gio.DBusProxyFlags.NONE,
            None,
            self.PORTAL_BUS,
            self.PORTAL_PATH,
            self.PORTAL_IFACE,
            None,
        )

    def initialize(self, persist_mode: int = 0) -> None:
        """
        Initialize portal session

        Args:
            persist_mode: Permission persistence mode
                0 = Never persist (dialog every time)
                1 = Persist while app running
                2 = Persist until revoked (recommended)

        Raises:
            PermissionDenied: User denied permission
            SessionError: Session creation failed
            RuntimeError: Not running on Wayland

        Example:
            >>> ctrl = WaylandInput()
            >>> ctrl.initialize(persist_mode=2)  # Approve once
            >>> # Future runs will auto-restore
        """
        if self._initialized:
            return

        self._ensure_dbus()

        # Create new session
        self._create_session(persist_mode)
        self._initialized = True

    def close(self) -> None:
        """Release resources and close session"""
        if self._session_handle and self._portal:
            try:
                self._portal.call_sync(
                    "Close",
                    GLib.Variant("(o)", (self._session_handle,)),
                    Gio.DBusCallFlags.NONE,
                    5000,
                    None,
                )
            except Exception:
                pass  # Ignore errors during cleanup

        self._session_handle = None
        self._initialized = False

    # === Input Methods ===

    def click(self, point: Point, button: int = 1) -> None:
        """
        Click at screen coordinates

        Args:
            point: Screen coordinates (x, y)
            button: Mouse button (1=left, 2=middle, 3=right)

        Raises:
            RuntimeError: Not initialized
            InputError: Click failed

        Example:
            >>> ctrl.click(Point(500, 500))  # Left click center
            >>> ctrl.click(Point(100, 100), button=3)  # Right click
        """
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")

        delay = getattr(self, "_pause", 0.05) or 0.05
        try:
            self._notify_pointer_motion_absolute(point.x, point.y)
            time.sleep(delay)  # Small delay between move and click
            self._notify_pointer_button(button, pressed=True)
            time.sleep(delay)
            self._notify_pointer_button(button, pressed=False)
        except Exception as e:
            raise InputError(f"Click failed: {e}") from e

    def move_mouse(self, point: Point) -> None:
        """
        Move mouse cursor to coordinates

        Args:
            point: Target coordinates

        Raises:
            RuntimeError: Not initialized
            InputError: Move failed
        """
        if not self._initialized:
            raise RuntimeError("Not initialized")

        try:
            self._notify_pointer_motion_absolute(point.x, point.y)
        except Exception as e:
            raise InputError(f"Mouse move failed: {e}") from e


    def type_text(self, text: str, interval: float = 0.01) -> None:
        """
        Type text string

        Args:
            text: Unicode text to type
            interval: Delay between characters (seconds)

        Raises:
            RuntimeError: Not initialized
            InputError: Typing failed

        Example:
            >>> ctrl.type_text("Hello World!")
            >>> ctrl.type_text("Fast typing", interval=0.001)
        """
        if not self._initialized:
            raise RuntimeError("Not initialized")

        for char in text:
            try:
                self._notify_keyboard_keysym(char, pressed=True)
                time.sleep(interval)
                self._notify_keyboard_keysym(char, pressed=False)
            except Exception as e:
                raise InputError(f"Typing failed at char '{char}': {e}") from e

    def press_key(self, key: str) -> None:
        """
        Press and release a single key

        Args:
            key: Key name (e.g., "Return", "Escape", "a")

        Raises:
            RuntimeError: Not initialized
            InputError: Key press failed

        Example:
            >>> ctrl.press_key("Return")  # Press Enter
            >>> ctrl.press_key("Escape")  # Press Esc
        """
        if not self._initialized:
            raise RuntimeError("Not initialized")

        key = normalize_key(key)
        delay = getattr(self, "_pause", 0.05) or 0.05

        try:
            self._notify_keyboard_keysym(key, pressed=True)
            time.sleep(delay)
            self._notify_keyboard_keysym(key, pressed=False)
        except Exception as e:
            raise InputError(f"Key press failed: {e}") from e

    def key_combo(self, keys: List[str]) -> None:
        """
        Press multiple keys together (combination)

        Args:
            keys: List of keys to press together
                 (e.g., ["Control", "a"], ["Alt", "Tab"])

        Raises:
            RuntimeError: Not initialized
            InputError: Key combo failed

        Example:
            >>> ctrl.key_combo(["Control", "a"])  # Select all
            >>> ctrl.key_combo(["Control", "c"])  # Copy
            >>> ctrl.key_combo(["Alt", "Tab"])    # Switch window
        """
        if not self._initialized:
            raise RuntimeError("Not initialized")

        has_shift = any(normalize_key(k) == "Shift" for k in keys)
        normalized_keys = []
        for k in keys:
            nk = normalize_key(k)
            if len(nk) == 1 and nk.isupper() and not has_shift:
                nk = nk.lower()
            normalized_keys.append(nk)
        keys = normalized_keys
        delay = getattr(self, "_pause", 0.05) or 0.05

        try:
            # Press all keys
            for key in keys:
                self._notify_keyboard_keysym(key, pressed=True)
                time.sleep(delay)

            # Release in reverse order
            for key in reversed(keys):
                self._notify_keyboard_keysym(key, pressed=False)
                time.sleep(delay)



        except Exception as e:
            raise InputError(f"Key combo failed: {e}") from e

    # === Private Portal Methods ===

    def _create_session(self, persist_mode: int) -> None:
        """Create new portal session"""
        token = uuid.uuid4().hex[:8]
        options = {
            "session_handle_token": GLib.Variant("s", f"open_alo_{token}"),
            "handle_token": GLib.Variant("s", f"req_{token}"),
        }

        error_code, results = portal_request(
            self._bus,
            self._portal,
            "CreateSession",
            GLib.Variant("(a{sv})", (options,)),
        )

        if error_code != 0:
            if error_code == 1:
                raise PermissionDenied("User denied permission")
            elif error_code == 2:
                raise SessionError("Portal request canceled")
            raise SessionError(f"Failed to create session (code: {error_code})")

        if results is None:
            raise SessionError("No response from portal (timeout)")

        session_handle = str(results["session_handle"])
        self._session_handle = session_handle

        # Select input devices
        self._select_devices(persist_mode)

    def _select_devices(self, persist_mode: int) -> None:
        """Select input devices (keyboard, mouse)"""
        dev_token = uuid.uuid4().hex[:8]
        options = {
            "types": GLib.Variant("u", 7),  # Keyboard | Pointer | Touchscreen
            "handle_token": GLib.Variant("s", f"dev_{dev_token}"),
        }

        if persist_mode > 0:
            options["persist_mode"] = GLib.Variant("u", persist_mode)

            # Check for existing token
            token = self._load_token()
            if token:
                options["restore_token"] = GLib.Variant("s", token)

        error_code, results = portal_request(
            self._bus,
            self._portal,
            "SelectDevices",
            GLib.Variant("(oa{sv})", (self._session_handle, options)),
        )

        if error_code != 0:
            raise PermissionDenied("User denied device access")

        # Save token for future sessions
        if persist_mode > 0 and results and "restore_token" in results:
            restore_token = results["restore_token"]
            if hasattr(restore_token, "get_string"):
                restore_token = restore_token.get_string()
            self._save_token(str(restore_token))


        # Start the remote desktop session
        self._start_session()

    def _start_session(self) -> None:
        """Start the remote desktop session"""
        start_token = uuid.uuid4().hex[:8]
        options = {
            "handle_token": GLib.Variant("s", f"start_{start_token}"),
        }

        error_code, _ = portal_request(
            self._bus,
            self._portal,
            "Start",
            GLib.Variant("(osa{sv})", (self._session_handle, "", options)),
        )

        if error_code != 0:
            raise SessionError("Failed to start remote desktop session")

    def _load_token(self) -> Optional[str]:
        """Load restore token from disk"""
        try:
            if self._token_path.exists():
                data = json.loads(self._token_path.read_text())
                return data.get("restore_token")
        except Exception:
            pass
        return None

    def _save_token(self, token: str) -> None:
        """Save restore token to disk"""
        try:
            self._token_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "restore_token": token,
                "timestamp": time.time(),
                "version": 1,
            }
            self._token_path.write_text(json.dumps(data))
        except Exception:
            pass  # Token save failure is not fatal

    def _notify_pointer_motion_absolute(self, x: float, y: float) -> None:
        """Send absolute pointer motion event to portal"""
        options = {}
        try:
            self._portal.call_sync(
                "NotifyPointerMotionAbsolute",
                GLib.Variant(
                    "(oa{sv}udd)",
                    (self._session_handle, options, 0, float(x), float(y)),
                ),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except Exception:
            try:
                self._portal.call_sync(
                    "NotifyPointerMotionAbsolute",
                    GLib.Variant(
                        "(oa{sv}dd)",
                        (self._session_handle, options, float(x), float(y)),
                    ),
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None,
                )
            except Exception as e_abs:
                raise InputError(
                    f"Absolute pointer motion failed on portal: {e_abs}"
                ) from e_abs


    def _notify_pointer_motion(self, x: int, y: int) -> None:
        """Send pointer motion event to portal"""
        options = {}
        self._portal.call_sync(
            "NotifyPointerMotion",
            GLib.Variant(
                "(oa{sv}dd)", (self._session_handle, options, float(x), float(y))
            ),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )


    def _notify_pointer_button(self, button: int, pressed: bool) -> None:
        """Send pointer button event (mapped to evdev codes, see EVDEV_BUTTON_MAP)"""
        options = {}
        state = 1 if pressed else 0
        evdev_code = EVDEV_BUTTON_MAP.get(button, button if button >= 0x100 else 0x110)
        self._portal.call_sync(
            "NotifyPointerButton",
            GLib.Variant(
                "(oa{sv}iu)",
                (self._session_handle, options, int(evdev_code), int(state)),
            ),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

    def _notify_keyboard_keysym(self, key: str, pressed: bool) -> None:
        """
        Send keyboard key event using X11 keysym (via NotifyKeyboardKeysym)

        Fixes legacy bug: old code used NotifyKeyboardKeycode with hardcoded
        keycode=0, which made all keyboard input non-functional.
        Now uses NotifyKeyboardKeysym like UnifiedRemoteDesktop.
        """
        options = {}
        state = 1 if pressed else 0
        keysym = char_to_keysym(key)

        self._portal.call_sync(
            "NotifyKeyboardKeysym",
            GLib.Variant("(oa{sv}iu)", (self._session_handle, options, keysym, state)),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
