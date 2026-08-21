"""
Unified Remote Desktop using RemoteDesktop Portal

Provides both input control AND screen capture in a single permission.
This is the modern approach used by RustDesk and other remote desktop solutions.

Key features:
- Single permission dialog for everything
- Real-time screen streaming via PipeWire
- Screenshot capability
- Full keyboard and mouse control
- Persistent permission tokens
"""

import json
import time
import uuid
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import Generator, List, Optional, Tuple

import gi

gi.require_version("Gst", "1.0")
gi.require_version("GLib", "2.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib, Gst

from ..exceptions import CaptureError, InputError, PermissionDenied, SessionError
from ..types import Point, normalize_key
from ._portal_helpers import char_to_keysym, portal_request

# Initialize GStreamer
Gst.init(None)


class UnifiedRemoteDesktop:
    """
    Unified remote desktop session using RemoteDesktop portal.

    Provides both input control AND screen capture in a single permission.
    Perfect for AI agents that need to see and control the desktop.

    Features:
    - Real-time screen streaming (PipeWire)
    - Screenshot capture
    - Mouse control (move, click, drag)
    - Keyboard control (type, press keys, combos)
    - Single permission dialog
    - Persistent permissions

    Example:
        >>> with UnifiedRemoteDesktop() as desktop:
        ...     desktop.initialize(persist_mode=2)  # One permission for all
        ...
        ...     # Control input
        ...     desktop.click(Point(500, 500))
        ...     desktop.type_text("Hello World")
        ...
        ...     # Capture screen
        ...     screenshot = desktop.capture_screenshot()
        ...
        ...     # Get live stream
        ...     frame = desktop.get_frame()
    """

    PORTAL_BUS = "org.freedesktop.portal.Desktop"
    PORTAL_PATH = "/org/freedesktop/portal/desktop"
    REMOTEDESKTOP_IFACE = "org.freedesktop.portal.RemoteDesktop"
    SCREENCAST_IFACE = "org.freedesktop.portal.ScreenCast"

    # Device types for SelectDevices
    DEVICE_KEYBOARD = 1
    DEVICE_POINTER = 2
    DEVICE_TOUCHSCREEN = 4
    DEVICE_ALL = 7  # Keyboard | Pointer | Touchscreen

    # Source types for SelectSources
    SOURCE_MONITOR = 1
    SOURCE_WINDOW = 2
    SOURCE_VIRTUAL = 4

    def __init__(self, token_path: Optional[Path] = None):
        """
        Initialize unified remote desktop controller

        Args:
            token_path: Path to store permission tokens.
                       None = ~/.config/open_alo_core/unified_token.json
        """
        self._session_handle: Optional[str] = None
        self._pipewire_node: Optional[int] = None
        self._initialized = False

        # Token storage
        if token_path is None:
            token_path = (
                Path.home() / ".config" / "open_alo_core" / "unified_token.json"
            )
        self._token_path = Path(token_path)

        # D-Bus connection (lazy initialization)
        self._bus: Optional[Gio.DBusConnection] = None
        self._portal: Optional[Gio.DBusProxy] = None  # RemoteDesktop portal
        self._screencast_portal: Optional[Gio.DBusProxy] = None  # ScreenCast portal

        # GStreamer pipeline for capture
        self._pipeline: Optional[Gst.Pipeline] = None
        self._appsink: Optional[Gst.Element] = None

        # Config properties
        self._pause = 0.05
        self._fail_safe = False
        self._touch_mode = False

    def __enter__(self) -> "UnifiedRemoteDesktop":
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

        # RemoteDesktop portal for input + session management
        self._portal = Gio.DBusProxy.new_sync(
            self._bus,
            Gio.DBusProxyFlags.NONE,
            None,
            self.PORTAL_BUS,
            self.PORTAL_PATH,
            self.REMOTEDESKTOP_IFACE,
            None,
        )

        # ScreenCast portal for source selection
        # (RemoteDesktop inherits ScreenCast but SelectSources is on ScreenCast interface)
        self._screencast_portal = Gio.DBusProxy.new_sync(
            self._bus,
            Gio.DBusProxyFlags.NONE,
            None,
            self.PORTAL_BUS,
            self.PORTAL_PATH,
            self.SCREENCAST_IFACE,
            None,
        )

    # ==================== Session Management ====================

    def initialize(self, persist_mode: int = 2, enable_capture: bool = True) -> bool:
        """
        Initialize unified remote desktop session

        Shows ONE permission dialog for both input and screen capture.

        Args:
            persist_mode: Permission persistence
                0 = Never persist (dialog every time)
                1 = Persist while app running
                2 = Persist until revoked (recommended)
            enable_capture: Enable screen capture (True for agents)

        Returns:
            True if initialization succeeded

        Raises:
            PermissionDenied: User denied permission
            SessionError: Session creation failed

        Example:
            >>> desktop.initialize(persist_mode=2)  # One dialog, approve once
        """
        if self._initialized:
            return True

        self._ensure_dbus()

        # Create new session with both capabilities
        self._create_session(persist_mode, enable_capture)
        self._initialized = True
        return True

    def close(self) -> None:
        """Release resources and close session"""
        # Stop GStreamer pipeline
        if self._pipeline:
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None
            self._appsink = None

        # Close portal session
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
                pass

        self._session_handle = None
        self._pipewire_node = None
        self._initialized = False

    # ==================== Input Control ====================

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
            >>> desktop.click(Point(500, 500))  # Left click
            >>> desktop.click(Point(100, 100), button=3)  # Right click
        """
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")

        delay = self._pause if self._pause > 0 else 0.05
        try:
            self._notify_pointer_motion_absolute(point.x, point.y)
            time.sleep(delay)
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

        Example:
            >>> desktop.move_mouse(Point(800, 600))
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

        Example:
            >>> desktop.type_text("Hello World!")
            >>> desktop.type_text("Fast", interval=0.001)
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

        Example:
            >>> desktop.press_key("Return")  # Enter
            >>> desktop.press_key("Escape")  # Esc
        """
        if not self._initialized:
            raise RuntimeError("Not initialized")

        key = normalize_key(key)
        delay = self._pause if self._pause > 0 else 0.05

        try:
            self._notify_keyboard_keysym(key, pressed=True)
            time.sleep(delay)
            self._notify_keyboard_keysym(key, pressed=False)
        except Exception as e:
            raise InputError(f"Key press failed: {e}") from e

    def key_combo(self, keys: List[str]) -> None:
        """
        Press multiple keys together (keyboard shortcut)

        Args:
            keys: List of keys to press together

        Example:
            >>> desktop.key_combo(["Control", "a"])  # Select all
            >>> desktop.key_combo(["Control", "c"])  # Copy
            >>> desktop.key_combo(["Alt", "Tab"])    # Switch window
        """
        if not self._initialized:
            raise RuntimeError("Not initialized")

        keys = [normalize_key(k) for k in keys]
        delay = self._pause if self._pause > 0 else 0.05

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


    def scroll(
        self, clicks: int, x: Optional[int] = None, y: Optional[int] = None
    ) -> None:
        """
        Scroll vertically (mouse wheel).

        Args:
            clicks: Number of wheel clicks. Positive = scroll up, Negative = scroll down.
            x: Optional X coordinate to move cursor before scrolling.
            y: Optional Y coordinate to move cursor before scrolling.

        Raises:
            InputError: Scroll failed

        Example:
            >>> desktop.scroll(-3)            # Scroll down 3 clicks
            >>> desktop.scroll(5, x=100, y=200)  # Move to (100,200) then scroll up
        """
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")
        try:
            if x is not None and y is not None:
                self._notify_pointer_motion(x, y)
                time.sleep(self._pause)
            self._portal.call_sync(
                "NotifyPointerAxisDiscrete",
                GLib.Variant("(oa{sv}ui)", (self._session_handle, {}, 0, clicks)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except Exception as e:
            raise InputError(f"Scroll failed: {e}") from e

    def hscroll(
        self, clicks: int, x: Optional[int] = None, y: Optional[int] = None
    ) -> None:
        """Horizontal scroll. Positive=right, Negative=left."""
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")
        try:
            if x is not None and y is not None:
                self._notify_pointer_motion(x, y)
                time.sleep(self._pause)
            self._portal.call_sync(
                "NotifyPointerAxisDiscrete",
                GLib.Variant("(oa{sv}ui)", (self._session_handle, {}, 1, clicks)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except Exception as e:
            raise InputError(f"Horizontal scroll failed: {e}") from e

    def smooth_scroll(self, dx: float = 0, dy: float = 0, finish: bool = False) -> None:
        """Smooth scroll (touchpad-style)."""
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")
        try:
            options = {}
            if finish:
                options["finish"] = GLib.Variant("b", True)
            self._portal.call_sync(
                "NotifyPointerAxis",
                GLib.Variant("(oa{sv}dd)", (self._session_handle, options, dx, dy)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except Exception as e:
            raise InputError(f"Smooth scroll failed: {e}") from e

    def drag(
        self, start: Point, end: Point, button: int = 1, duration: float = 0.0
    ) -> None:
        """Drag from start to end with button held."""
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")
        button_pressed = False
        try:
            self._notify_pointer_motion(start.x, start.y)
            time.sleep(self._pause)
            self._notify_pointer_button(button, pressed=True)
            button_pressed = True
            time.sleep(self._pause)
            if duration > 0:
                steps = max(int(duration / 0.05), 5)
                for i in range(1, steps + 1):
                    t = i / steps
                    x = int(start.x + (end.x - start.x) * t)
                    y = int(start.y + (end.y - start.y) * t)
                    self._notify_pointer_motion(x, y)
                    time.sleep(self._pause)
            else:
                self._notify_pointer_motion(end.x, end.y)
                time.sleep(self._pause)
        except Exception as e:
            raise InputError(f"Drag failed: {e}") from e
        finally:
            if button_pressed:
                try:
                    self._notify_pointer_button(button, pressed=False)
                except Exception:
                    pass

    def swipe(
        self,
        start: Point,
        end: Point,
        duration: float = 0.3,
        button: int = 1,
        steps: int = 10,
    ) -> None:
        """Smooth drag with intermediate steps for natural motion."""
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")
        button_pressed = False
        try:
            self._notify_pointer_motion(start.x, start.y)
            time.sleep(self._pause)
            self._notify_pointer_button(button, pressed=True)
            button_pressed = True
            time.sleep(self._pause)
            for i in range(1, steps + 1):
                t = i / steps
                x = int(start.x + (end.x - start.x) * t)
                y = int(start.y + (end.y - start.y) * t)
                self._notify_pointer_motion(x, y)
                time.sleep(duration / steps)
        except Exception as e:
            raise InputError(f"Swipe failed: {e}") from e
        finally:
            if button_pressed:
                try:
                    self._notify_pointer_button(button, pressed=False)
                except Exception:
                    pass


    @contextmanager
    def hold_key(self, key: str) -> Generator[None, None, None]:
        """Context manager that holds a key while inside the block."""
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")
        key = normalize_key(key)
        try:
            self._notify_keyboard_keysym(key, pressed=True)
            time.sleep(self._pause)
            yield
        finally:
            self._notify_keyboard_keysym(key, pressed=False)
            time.sleep(self._pause)

    def double_click(
        self, point: Point, button: int = 1, interval: float = 0.1
    ) -> None:
        """Two rapid clicks at position."""
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")
        self.click(point, button)
        time.sleep(interval)
        self.click(point, button)

    def move_mouse_relative(self, dx: int, dy: int) -> None:
        """Move mouse relative to current position."""
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")
        try:
            self._portal.call_sync(
                "NotifyPointerMotion",
                GLib.Variant(
                    "(oa{sv}dd)", (self._session_handle, {}, float(dx), float(dy))
                ),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except Exception as e:
            raise InputError(f"Relative move failed: {e}") from e

    def press_keys(self, keys: List[str], interval: float = 0.1) -> None:
        """Press multiple keys in sequence."""
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")
        for key in keys:
            self.press_key(key)
            time.sleep(interval)

    # ==================== Screen Capture ====================

    def capture_screenshot(self) -> bytes:
        """
        Capture a single screenshot (PNG)

        Returns:
            PNG image data as bytes

        Raises:
            RuntimeError: Not initialized or capture not enabled
            CaptureError: Screenshot failed

        Example:
            >>> screenshot = desktop.capture_screenshot()
            >>> Path("/tmp/shot.png").write_bytes(screenshot)
        """
        if not self._initialized:
            raise RuntimeError("Not initialized")

        if self._pipewire_node is None:
            raise RuntimeError(
                "Screen capture not enabled - initialize with enable_capture=True"
            )

        try:
            # Ensure pipeline is running
            self._ensure_pipeline()

            # Get a frame from the appsink
            sample = self._appsink.emit("pull-sample")
            if not sample:
                raise CaptureError("No sample available")

            buffer = sample.get_buffer()
            if not buffer:
                raise CaptureError("No buffer in sample")

            # Extract PNG data
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if not success:
                raise CaptureError("Failed to map buffer")

            try:
                png_data = bytes(map_info.data)
                return png_data
            finally:
                buffer.unmap(map_info)

        except CaptureError:
            raise
        except Exception as e:
            raise CaptureError(f"Screenshot failed: {e}") from e

    def get_frame(self) -> Optional[bytes]:
        """
        Get the latest frame from live stream (for real-time streaming)

        Returns:
            PNG frame data or None if no frame available

        Note:
            This method is non-blocking. For continuous streaming, call repeatedly.
            For a guaranteed frame, use capture_screenshot() instead.

        Example:
            >>> while True:
            ...     frame = desktop.get_frame()
            ...     if frame:
            ...         send_to_client(frame)
        """
        if not self._initialized or self._pipewire_node is None:
            return None

        try:
            # Ensure pipeline is running
            self._ensure_pipeline()

            # Try to pull latest sample (non-blocking with short timeout)
            sample = self._appsink.emit("try-pull-sample", 1000000)  # 1ms timeout
            if not sample:
                return None

            buffer = sample.get_buffer()
            if not buffer:
                return None

            success, map_info = buffer.map(Gst.MapFlags.READ)
            if not success:
                return None

            try:
                png_data = bytes(map_info.data)
                return png_data
            finally:
                buffer.unmap(map_info)

        except Exception:
            return None

    def get_screen_size(self) -> Optional[Tuple[int, int]]:
        """
        Get screen resolution

        Returns:
            (width, height) or None if not available
        """
        try:
            self._ensure_pipeline()
        except Exception:
            return None

        if not self._pipeline:
            return None

        # Get caps from pipeline
        try:
            pad = self._appsink.get_static_pad("sink")
            caps = pad.get_current_caps()
            if caps:
                struct = caps.get_structure(0)
                width = struct.get_int("width")[1]
                height = struct.get_int("height")[1]
                return (width, height)
        except Exception:
            pass

        return None


    # ==================== Internal Session Management ====================

    def _create_session(self, persist_mode: int = 2, enable_capture: bool = True) -> None:
        """Create unified session with both input and capture"""
        token = uuid.uuid4().hex[:8]
        options = {
            "session_handle_token": GLib.Variant("s", f"unified_{token}"),
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
            raise SessionError(f"Failed to create session (code: {error_code})")

        if results is None:
            raise SessionError("No response from portal (timeout)")

        session_handle = str(results["session_handle"])
        self._session_handle = session_handle

        # Select input devices (keyboard/mouse)
        self._select_devices(persist_mode)

        # Select capture sources (if enabled)
        if enable_capture:
            self._select_sources()

        # Start the unified session (shows permission dialog)
        self._start_session(enable_capture=enable_capture)

    def _select_devices(self, persist_mode: int) -> None:
        """Select input devices (keyboard, mouse, touchscreen)"""
        dev_token = uuid.uuid4().hex[:8]
        options = {
            "types": GLib.Variant("u", self.DEVICE_ALL),
            "handle_token": GLib.Variant("s", f"dev_{dev_token}"),
        }

        if persist_mode > 0:
            options["persist_mode"] = GLib.Variant("u", persist_mode)

            # Pass restore token if available
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

        # Save restore token from response
        if persist_mode > 0 and results is not None and "restore_token" in results:
            restore_token = results["restore_token"]
            if hasattr(restore_token, "get_string"):
                restore_token = restore_token.get_string()
            self._save_token(str(restore_token))

    def _select_sources(self) -> None:
        """Select capture sources (monitor/window)"""
        src_token = uuid.uuid4().hex[:8]
        options = {
            "types": GLib.Variant("u", self.SOURCE_MONITOR),
            "multiple": GLib.Variant("b", False),
            "cursor_mode": GLib.Variant("u", 2),  # Embedded
            "handle_token": GLib.Variant("s", f"src_{src_token}"),
        }

        # SelectSources is called on ScreenCast interface, not RemoteDesktop
        error_code, _ = portal_request(
            self._bus,
            self._screencast_portal,
            "SelectSources",
            GLib.Variant("(oa{sv})", (self._session_handle, options)),
        )

        if error_code != 0:
            raise PermissionDenied("User denied source selection")

    def _start_session(self, enable_capture: bool = True) -> None:
        """Start the unified session - shows permission dialog"""
        start_token = uuid.uuid4().hex[:8]
        options = {
            "handle_token": GLib.Variant("s", f"start_{start_token}"),
        }

        error_code, results = portal_request(
            self._bus,
            self._portal,
            "Start",
            GLib.Variant("(osa{sv})", (self._session_handle, "", options)),
        )

        if error_code != 0 or results is None:
            raise SessionError(f"Failed to start session (error code {error_code})")

        # Extract PipeWire node ID for capture
        if results and enable_capture:
            streams = results.get("streams")
            if streams and len(streams) > 0:
                stream_info = streams[0]
                if isinstance(stream_info, tuple) and len(stream_info) >= 1:
                    self._pipewire_node = int(stream_info[0])
                    # Pipeline is created lazily on first capture


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
            pass

    def _ensure_pipeline(self) -> None:
        """Ensure GStreamer pipeline is running (creates one if needed)"""
        if self._pipeline is not None:
            state = self._pipeline.get_state(0)[1]
            if state == Gst.State.PLAYING:
                return

        if self._pipewire_node is None:
            raise CaptureError("No PipeWire node available")

        # Build pipeline: pipewiresrc → videoconvert → pngenc → appsink
        pipeline_str = (
            f"pipewiresrc path={self._pipewire_node} ! "
            "videoconvert ! "
            "video/x-raw,format=RGB ! "
            "pngenc ! "
            "appsink name=sink emit-signals=true max-buffers=1 drop=true"
        )

        try:
            self._pipeline = Gst.parse_launch(pipeline_str)
            self._appsink = self._pipeline.get_by_name("sink")

            # Start pipeline
            ret = self._pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise CaptureError("Failed to start GStreamer pipeline")

            # Wait for pipeline to be ready
            time.sleep(0.5)

        except Exception as e:
            raise CaptureError(f"Failed to setup GStreamer pipeline: {e}")

    # ==================== Private Input Methods ====================

    def _notify_pointer_motion_absolute(self, x: float, y: float) -> None:
        """Send absolute pointer motion event via RemoteDesktop portal"""
        options = {}
        stream_id = getattr(self, "_pipewire_node", 0) or 0
        try:
            self._portal.call_sync(
                "NotifyPointerMotionAbsolute",
                GLib.Variant(
                    "(oa{sv}udd)",
                    (self._session_handle, options, int(stream_id), float(x), float(y)),
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
        """Send relative pointer motion event"""
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
        """Send pointer button event"""
        options = {}
        state = 1 if pressed else 0
        self._portal.call_sync(
            "NotifyPointerButton",
            GLib.Variant(
                "(oa{sv}iu)", (self._session_handle, options, int(button), int(state))
            ),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

    def _notify_keyboard_keysym(self, key: str, pressed: bool) -> None:
        """Send keyboard key event using keysym"""
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

    # ==================== Config Properties ====================

    @property
    def pause(self) -> float:
        """Delay between actions (seconds). Default 0.05."""
        return self._pause

    @pause.setter
    def pause(self, value: float) -> None:
        self._pause = max(0.0, float(value))

    @property
    def fail_safe(self) -> bool:
        """Enable fail-safe mode. When True, raise FailSafeException on abort."""
        return self._fail_safe

    @fail_safe.setter
    def fail_safe(self, value: bool) -> None:
        self._fail_safe = bool(value)

    @property
    def touch_mode(self) -> bool:
        """When True, use touch events instead of mouse."""
        return self._touch_mode

    @touch_mode.setter
    def touch_mode(self, value: bool) -> None:
        self._touch_mode = bool(value)


# ==================== Convenience Functions ====================


def create_unified_desktop(
    persist_mode: int = 2, enable_capture: bool = True
) -> UnifiedRemoteDesktop:
    """
    Convenience function to create and initialize unified desktop

    Args:
        persist_mode: Permission persistence mode (0-2)
        enable_capture: Enable screen capture

    Returns:
        Initialized UnifiedRemoteDesktop instance

    Example:
        >>> desktop = create_unified_desktop()
        >>> desktop.click(Point(500, 500))
        >>> screenshot = desktop.capture_screenshot()
        >>> desktop.close()
    """
    desktop = UnifiedRemoteDesktop()
    desktop.initialize(persist_mode=persist_mode, enable_capture=enable_capture)
    return desktop
