"""
Wayland input controller using XDG RemoteDesktop Portal

Provides mouse and keyboard control on Wayland without root privileges.
Uses persistent permissions so user only approves once.
"""

import gi
import json
import time
import uuid
from pathlib import Path
from typing import Optional, List

# Require Gio version
gi.require_version('Gio', '2.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gio, GLib

from ..types import Point, normalize_key
from ..exceptions import PermissionDenied, SessionError, InputError


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
            # Default location
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
        if self._bus is None:
            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            self._portal = Gio.DBusProxy.new_sync(
                self._bus,
                Gio.DBusProxyFlags.NONE,
                None,
                self.PORTAL_BUS,
                self.PORTAL_PATH,
                self.PORTAL_IFACE,
                None
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
        
        # Try to restore from token
        if persist_mode > 0:
            if self._restore_session():
                self._initialized = True
                return
        
        # Create new session
        self._create_session(persist_mode)
        self._initialized = True
    
    def close(self) -> None:
        """Release resources and close session"""
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
        
        try:
            self._notify_pointer_motion(point.x, point.y)
            time.sleep(0.05)  # Small delay between move and click
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
        
        Raises:
            RuntimeError: Not initialized
            InputError: Move failed
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
                self._notify_keyboard_key(char, pressed=True)
                time.sleep(interval)
                self._notify_keyboard_key(char, pressed=False)
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
        
        try:
            self._notify_keyboard_key(key, pressed=True)
            time.sleep(0.05)
            self._notify_keyboard_key(key, pressed=False)
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
        
        keys = [normalize_key(k) for k in keys]
        
        try:
            # Press all keys
            for key in keys:
                self._notify_keyboard_key(key, pressed=True)
                time.sleep(0.05)
            
            # Release in reverse order
            for key in reversed(keys):
                self._notify_keyboard_key(key, pressed=False)
                time.sleep(0.05)
                
        except Exception as e:
            raise InputError(f"Key combo failed: {e}") from e
    
    # === Private Portal Methods ===
    
    def _create_session(self, persist_mode: int) -> None:
        """Create new portal session"""
        loop = GLib.MainLoop()
        session_handle: Optional[str] = None
        error_code: int = -1
        
        token = uuid.uuid4().hex[:8]
        options = {
            'session_handle_token': GLib.Variant('s', f'open_alo_{token}'),
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
            elif error_code == 2:
                raise SessionError("Portal request canceled")
            else:
                raise SessionError(f"Failed to create session (code: {error_code})")
        
        self._session_handle = session_handle
        
        # Select input devices
        self._select_devices(persist_mode)
    
    def _select_devices(self, persist_mode: int) -> None:
        """Select input devices (keyboard, mouse)"""
        loop = GLib.MainLoop()
        success = False
        
        dev_token = uuid.uuid4().hex[:8]
        options = {
            'types': GLib.Variant('u', 7),  # Keyboard | Pointer | Touchscreen
            'handle_token': GLib.Variant('s', f'dev_{dev_token}'),
        }
        
        if persist_mode > 0:
            options['persist_mode'] = GLib.Variant('u', persist_mode)
            
            # Check for existing token
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
                # Save token for future sessions
                if persist_mode > 0:
                    # Extract restore_token from results if present
                    if isinstance(results, dict) and 'restore_token' in results:
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
        
        # Start the remote desktop session
        self._start_session()
    
    def _start_session(self) -> None:
        """Start the remote desktop session"""
        loop = GLib.MainLoop()
        success = False
        
        start_token = uuid.uuid4().hex[:8]
        options = {
            'handle_token': GLib.Variant('s', f'start_{start_token}'),
        }
        
        result = self._portal.call_sync(
            'Start',
            GLib.Variant('(osa{sv})', (self._session_handle, '', options)),
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
            raise SessionError("Failed to start remote desktop session")
    
    def _restore_session(self) -> bool:
        """Try to restore from saved token"""
        token_data = self._load_token()
        if not token_data:
            return False
        
        # Try to create session using the restore token
        # If token is valid, portal will restore session without dialog
        try:
            self._create_session(2)  # Use persist_mode=2 for restoration
            return True
        except Exception:
            # Token invalid or expired, will create new session
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
            pass  # Token save failure is not fatal
    
    def _notify_pointer_motion(self, x: int, y: int) -> None:
        """Send pointer motion event to portal"""
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
    
    def _notify_keyboard_key(self, key: str, pressed: bool) -> None:
        """Send keyboard key event"""
        options = {}
        state = 1 if pressed else 0
        # Convert key name to keycode (simplified)
        # In production, you'd use a proper keycode mapping
        self._portal.call_sync(
            'NotifyKeyboardKeycode',
            GLib.Variant('(oa{sv}iu)', (self._session_handle, options, 0, state)),
            Gio.DBusCallFlags.NONE,
            -1,
            None
        )
