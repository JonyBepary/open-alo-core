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

import gi
import json
import time
import uuid
from pathlib import Path
from typing import Optional, List, Tuple
from io import BytesIO

# Require versions
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('Gio', '2.0')

from gi.repository import Gst, GLib, Gio

from ..types import Point, normalize_key
from ..exceptions import PermissionDenied, SessionError, InputError, CaptureError

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
            token_path = Path.home() / ".config" / "open_alo_core" / "unified_token.json"
        self._token_path = Path(token_path)

        # D-Bus connection (lazy initialization)
        self._bus: Optional[Gio.DBusConnection] = None
        self._portal: Optional[Gio.DBusProxy] = None  # RemoteDesktop portal
        self._screencast_portal: Optional[Gio.DBusProxy] = None  # ScreenCast portal

        # GStreamer pipeline for capture
        self._pipeline: Optional[Gst.Pipeline] = None
        self._appsink: Optional[Gst.Element] = None

    def __enter__(self) -> "UnifiedRemoteDesktop":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - auto cleanup"""
        self.close()
        return False

    def _ensure_dbus(self) -> None:
        """Lazy initialization of D-Bus connection"""
        if self._bus is None:
            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

            # RemoteDesktop portal for input + session management
            self._portal = Gio.DBusProxy.new_sync(
                self._bus,
                Gio.DBusProxyFlags.NONE,
                None,
                self.PORTAL_BUS,
                self.PORTAL_PATH,
                self.REMOTEDESKTOP_IFACE,
                None
            )

            # ScreenCast portal for source selection
            # (RemoteDesktop inherits ScreenCast but we call SelectSources on ScreenCast interface)
            self._screencast_portal = Gio.DBusProxy.new_sync(
                self._bus,
                Gio.DBusProxyFlags.NONE,
                None,
                self.PORTAL_BUS,
                self.PORTAL_PATH,
                self.SCREENCAST_IFACE,
                None
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

        # Try to restore from token
        if persist_mode > 0:
            if self._restore_session():
                self._initialized = True
                return True

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
                    'Close',
                    GLib.Variant('(o)', (self._session_handle,)),
                    Gio.DBusCallFlags.NONE,
                    5000,
                    None
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

        try:
            self._notify_pointer_motion(point.x, point.y)
            time.sleep(0.05)
            self._notify_pointer_button(button, pressed=True)
            time.sleep(0.05)
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
            self._notify_pointer_motion(point.x, point.y)
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

        try:
            self._notify_keyboard_keysym(key, pressed=True)
            time.sleep(0.05)
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

        try:
            # Press all keys
            for key in keys:
                self._notify_keyboard_keysym(key, pressed=True)
                time.sleep(0.05)

            # Release in reverse order
            for key in reversed(keys):
                self._notify_keyboard_keysym(key, pressed=False)
                time.sleep(0.05)

        except Exception as e:
            raise InputError(f"Key combo failed: {e}") from e

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
            raise RuntimeError("Screen capture not enabled - initialize with enable_capture=True")

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
            self._ensure_pipeline()

            # Try to pull sample (non-blocking)
            # Uses try-pull-sample which returns immediately if no frame buffered
            sample = self._appsink.emit("try-pull-sample", 0)
            if not sample:
                return None

            buffer = sample.get_buffer()
            if not buffer:
                return None

            success, map_info = buffer.map(Gst.MapFlags.READ)
            if not success:
                return None

            try:
                return bytes(map_info.data)
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

    # ==================== Private Portal Methods ====================

    def _create_session(self, persist_mode: int, enable_capture: bool) -> None:
        """Create unified session with both input and capture"""
        loop = GLib.MainLoop()
        session_handle: Optional[str] = None
        error_code: int = -1

        token = uuid.uuid4().hex[:8]
        options = {
            'session_handle_token': GLib.Variant('s', f'unified_{token}'),
            'handle_token': GLib.Variant('s', f'req_{token}')
        }

        result = self._portal.call_sync(
            'CreateSession',
            GLib.Variant('(a{sv})', (options,)),
            Gio.DBusCallFlags.NONE,
            10000,
            None
        )

        request_path = result[0]

        def on_response(conn, sender, path, iface, signal, params):
            nonlocal session_handle, error_code
            error_code, results = params
            if error_code == 0:
                session_handle = str(results['session_handle'])
            loop.quit()

        sub_id = self._bus.signal_subscribe(
            self.PORTAL_BUS,
            'org.freedesktop.portal.Request',
            'Response',
            request_path,
            None,
            Gio.DBusSignalFlags.NONE,
            on_response
        )

        GLib.timeout_add_seconds(30, loop.quit)
        loop.run()
        self._bus.signal_unsubscribe(sub_id)

        if session_handle is None:
            if error_code == 1:
                raise PermissionDenied("User denied permission")
            else:
                raise SessionError(f"Failed to create session (code: {error_code})")

        self._session_handle = session_handle

        # Select input devices (keyboard/mouse)
        self._select_devices(persist_mode)

        # Select capture sources (if enabled)
        if enable_capture:
            self._select_sources()

        # Start the unified session (shows permission dialog)
        self._start_session()

    def _select_devices(self, persist_mode: int) -> None:
        """Select input devices (keyboard, mouse, touchscreen)"""
        loop = GLib.MainLoop()
        success = False

        dev_token = uuid.uuid4().hex[:8]
        options = {
            'types': GLib.Variant('u', self.DEVICE_ALL),
            'handle_token': GLib.Variant('s', f'dev_{dev_token}'),
        }

        if persist_mode > 0:
            options['persist_mode'] = GLib.Variant('u', persist_mode)

            # Try to restore from token
            token = self._load_token()
            if token:
                options['restore_token'] = GLib.Variant('s', token)

        result = self._portal.call_sync(
            'SelectDevices',
            GLib.Variant('(oa{sv})', (self._session_handle, options)),
            Gio.DBusCallFlags.NONE,
            10000,
            None
        )

        request_path = result[0]

        def on_response(conn, sender, path, iface, signal, params):
            nonlocal success
            error_code, results = params
            if error_code == 0:
                success = True
                # Save restore token
                if persist_mode > 0 and isinstance(results, dict):
                    if 'restore_token' in results:
                        restore_token = results['restore_token']
                        if isinstance(restore_token, GLib.Variant):
                            restore_token = restore_token.get_string()
                        self._save_token(restore_token)
            loop.quit()

        sub_id = self._bus.signal_subscribe(
            self.PORTAL_BUS,
            'org.freedesktop.portal.Request',
            'Response',
            request_path,
            None,
            Gio.DBusSignalFlags.NONE,
            on_response
        )

        GLib.timeout_add_seconds(30, loop.quit)
        loop.run()
        self._bus.signal_unsubscribe(sub_id)

        if not success:
            raise PermissionDenied("User denied device access")

    def _select_sources(self) -> None:
        """Select capture sources (monitor/window)"""
        loop = GLib.MainLoop()
        success = False

        src_token = uuid.uuid4().hex[:8]
        options = {
            'types': GLib.Variant('u', self.SOURCE_MONITOR),
            'multiple': GLib.Variant('b', False),
            'cursor_mode': GLib.Variant('u', 2),  # Embedded
            'handle_token': GLib.Variant('s', f'src_{src_token}')
        }

        # SelectSources is called on ScreenCast interface, not RemoteDesktop
        result = self._screencast_portal.call_sync(
            'SelectSources',
            GLib.Variant('(oa{sv})', (self._session_handle, options)),
            Gio.DBusCallFlags.NONE,
            10000,
            None
        )

        request_path = result[0]

        def on_response(conn, sender, path, iface, signal, params):
            nonlocal success
            error_code, _ = params
            if error_code == 0:
                success = True
            loop.quit()

        sub_id = self._bus.signal_subscribe(
            self.PORTAL_BUS,
            'org.freedesktop.portal.Request',
            'Response',
            request_path,
            None,
            Gio.DBusSignalFlags.NONE,
            on_response
        )

        GLib.timeout_add_seconds(30, loop.quit)
        loop.run()
        self._bus.signal_unsubscribe(sub_id)

        if not success:
            raise PermissionDenied("User denied source selection")

    def _start_session(self) -> None:
        """Start the unified session - shows permission dialog"""
        loop = GLib.MainLoop()
        streams = None

        start_token = uuid.uuid4().hex[:8]
        options = {
            'handle_token': GLib.Variant('s', f'start_{start_token}'),
        }

        result = self._portal.call_sync(
            'Start',
            GLib.Variant('(osa{sv})', (self._session_handle, '', options)),
            Gio.DBusCallFlags.NONE,
            30000,
            None
        )

        request_path = result[0]

        def on_response(conn, sender, path, iface, signal, params):
            nonlocal streams
            error_code, results = params
            if error_code == 0:
                streams = results.get('streams')
            loop.quit()

        sub_id = self._bus.signal_subscribe(
            self.PORTAL_BUS,
            'org.freedesktop.portal.Request',
            'Response',
            request_path,
            None,
            Gio.DBusSignalFlags.NONE,
            on_response
        )

        GLib.timeout_add_seconds(30, loop.quit)
        loop.run()
        self._bus.signal_unsubscribe(sub_id)

        if streams is None:
            raise SessionError("Failed to start session")

        # Extract PipeWire node ID for capture
        if streams and len(streams) > 0:
            stream_info = streams[0]
            if isinstance(stream_info, tuple) and len(stream_info) >= 1:
                self._pipewire_node = int(stream_info[0])
                # Set up GStreamer pipeline for screen capture
                self._setup_gstreamer_pipeline()

    def _restore_session(self) -> bool:
        """Try to restore from saved token"""
        # For now, create new session
        # Token restoration would require full session restore logic
        return False

    def _load_token(self) -> Optional[str]:
        """Load restore token from disk"""
        try:
            if self._token_path.exists():
                data = json.loads(self._token_path.read_text())
                return data.get('restore_token')
        except Exception:
            pass
        return None

    def _save_token(self, token: str) -> None:
        """Save restore token to disk"""
        try:
            self._token_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'restore_token': token,
                'timestamp': time.time(),
                'version': 1
            }
            self._token_path.write_text(json.dumps(data))
        except Exception:
            pass

    def _setup_gstreamer_pipeline(self) -> None:
        """Set up GStreamer pipeline for screen capture"""
        if not self._pipewire_node:
            return

        # Create pipeline: PipeWire source → convert → PNG encode → appsink
        pipeline_str = (
            f'pipewiresrc path={self._pipewire_node} ! '
            f'videoconvert ! '
            f'video/x-raw,format=RGB ! '
            f'pngenc ! '
            f'appsink name=sink'
        )

        try:
            self._pipeline = Gst.parse_launch(pipeline_str)
            self._appsink = self._pipeline.get_by_name('sink')

            # Start pipeline
            self._pipeline.set_state(Gst.State.PLAYING)

            # Wait for pipeline to reach PLAYING state
            state_change = self._pipeline.get_state(Gst.CLOCK_TIME_NONE)
            if state_change[0] != Gst.StateChangeReturn.SUCCESS:
                raise CaptureError("Failed to start GStreamer pipeline")

        except Exception as e:
            raise CaptureError(f"Failed to setup GStreamer pipeline: {e}")

    # ==================== Private Input Methods ====================

    def _notify_pointer_motion(self, x: int, y: int) -> None:
        """Send pointer motion event"""
        options = {}
        self._portal.call_sync(
            'NotifyPointerMotion',
            GLib.Variant('(oa{sv}dd)', (self._session_handle, options, float(x), float(y))),
            Gio.DBusCallFlags.NONE,
            -1,
            None
        )

    def _notify_pointer_button(self, button: int, pressed: bool) -> None:
        """Send pointer button event"""
        options = {}
        state = 1 if pressed else 0
        self._portal.call_sync(
            'NotifyPointerButton',
            GLib.Variant('(oa{sv}iu)', (self._session_handle, options, int(button), int(state))),
            Gio.DBusCallFlags.NONE,
            -1,
            None
        )

    def _notify_keyboard_keysym(self, key: str, pressed: bool) -> None:
        """Send keyboard key event using keysym"""
        options = {}
        state = 1 if pressed else 0

        # Convert character to X11 keysym
        keysym = self._char_to_keysym(key)

        self._portal.call_sync(
            'NotifyKeyboardKeysym',
            GLib.Variant('(oa{sv}iu)', (self._session_handle, options, keysym, state)),
            Gio.DBusCallFlags.NONE,
            -1,
            None
        )

    def _char_to_keysym(self, char: str) -> int:
        """Convert character to X11 keysym"""
        # Simple mapping for common keys
        # In production, use a complete keysym table
        keysym_map = {
            'Return': 0xFF0D,
            'Escape': 0xFF1B,
            'Tab': 0xFF09,
            'BackSpace': 0xFF08,
            'Delete': 0xFFFF,
            'Left': 0xFF51,
            'Up': 0xFF52,
            'Right': 0xFF53,
            'Down': 0xFF54,
            'Control': 0xFFE3,
            'Alt': 0xFFE9,
            'Shift': 0xFFE1,
            'Super': 0xFFEB,
            ' ': 0x0020,
        }

        if char in keysym_map:
            return keysym_map[char]

        # For single characters, use Unicode value
        if len(char) == 1:
            return ord(char)

        return 0

    # ==================== Private Capture Methods ====================

    def _ensure_pipeline(self) -> None:
        """Ensure GStreamer pipeline is running"""
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
            "pngenc ! "
            "appsink name=sink emit-signals=true max-buffers=1 drop=true"
        )

        self._pipeline = Gst.parse_launch(pipeline_str)
        self._appsink = self._pipeline.get_by_name("sink")

        # Start pipeline
        ret = self._pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            raise CaptureError("Failed to start GStreamer pipeline")

        # Wait for pipeline to be ready
        time.sleep(0.5)


# ==================== Convenience Functions ====================

def create_unified_desktop(persist_mode: int = 2, enable_capture: bool = True) -> UnifiedRemoteDesktop:
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
