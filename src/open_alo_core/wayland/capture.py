"""
Wayland screen capture using PipeWire and XDG ScreenCast Portal

Provides native Wayland screenshot capability without X11 fallback.
"""

import gi
import time
import uuid
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

# Require versions
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('Gio', '2.0')

from gi.repository import Gst, GLib, Gio

from ..exceptions import CaptureError, PermissionDenied

# Initialize GStreamer
Gst.init(None)


@dataclass
class CaptureResult:
    """Result of screen capture operation"""
    data: bytes
    source_type: str  # 'monitor', 'window', 'camera'
    size: Tuple[int, int]
    
    def __repr__(self) -> str:
        return f"CaptureResult({len(self.data)} bytes, {self.source_type}, {self.size})"


class WaylandCapture:
    """
    Wayland screen capture using PipeWire and XDG ScreenCast Portal
    
    Features:
    - Native Wayland capture (no X11)
    - Monitor/window/camera source selection
    - PNG output
    - User approval via portal
    
    Example:
        >>> with WaylandCapture() as capture:
        ...     result = capture.capture_screen()
        ...     Path("/tmp/shot.png").write_bytes(result.data)
    
    Note:
        This creates a separate portal session from WaylandInput.
        In a future version, these may share a session for better UX.
    """
    
    PORTAL_BUS = "org.freedesktop.portal.Desktop"
    PORTAL_PATH = "/org/freedesktop/portal/desktop"
    PORTAL_IFACE = "org.freedesktop.portal.ScreenCast"
    
    def __init__(self):
        """Initialize capture controller"""
        self._session_handle: Optional[str] = None
        self._bus: Optional[Gio.DBusConnection] = None
        self._portal: Optional[Gio.DBusProxy] = None
    
    def __enter__(self) -> "WaylandCapture":
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - auto cleanup"""
        self.close()
        return False
    
    def _ensure_dbus(self) -> None:
        """Lazy initialization of D-Bus"""
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
    
    def capture_screen(self) -> CaptureResult:
        """
        Capture the screen
        
        This will show a permission dialog asking which screen/window
        to capture. The user must approve for the capture to proceed.
        
        Returns:
            CaptureResult with PNG data and metadata
        
        Raises:
            CaptureError: Capture failed
            PermissionDenied: User denied permission
        
        Example:
            >>> result = capture.capture_screen()
            >>> print(f"Captured {result.source_type}: {len(result.data)} bytes")
            >>> Path("/tmp/shot.png").write_bytes(result.data)
        """
        self._ensure_dbus()
        
        try:
            # Step 1: Create session
            self._create_session()
            
            # Step 2: Select sources
            self._select_sources()
            
            # Step 3: Start capture and get PipeWire node
            node_id, metadata = self._start_capture()
            
            # Step 4: Capture frame via GStreamer
            frame_data = self._capture_frame(node_id)
            
            # Determine source type and size
            source_type_id = metadata.get('source_type', 0)
            source_type = {1: 'monitor', 2: 'window', 3: 'camera'}.get(source_type_id, 'unknown')
            size = metadata.get('size', (0, 0))
            
            return CaptureResult(
                data=frame_data,
                source_type=source_type,
                size=size
            )
            
        except Exception as e:
            raise CaptureError(f"Screen capture failed: {e}") from e
        finally:
            self.close()
    
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
                pass
        
        self._session_handle = None
    
    def _create_session(self) -> None:
        """Create ScreenCast portal session"""
        loop = GLib.MainLoop()
        session_handle: Optional[str] = None
        error_code: int = -1
        
        token = uuid.uuid4().hex[:8]
        options = {
            'session_handle_token': GLib.Variant('s', f'cap_{token}'),
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
        
        GLib.timeout_add_seconds(15, loop.quit)
        loop.run()
        self._bus.signal_unsubscribe(sub_id)
        
        if session_handle is None:
            if error_code == 1:
                raise PermissionDenied("User denied screen capture permission")
            else:
                raise CaptureError(f"Failed to create session (code: {error_code})")
        
        self._session_handle = session_handle
    
    def _select_sources(self) -> None:
        """Select capture sources"""
        loop = GLib.MainLoop()
        success = False
        
        token = uuid.uuid4().hex[:8]
        options = {
            'types': GLib.Variant('u', 1),  # MONITOR
            'multiple': GLib.Variant('b', False),
            'cursor_mode': GLib.Variant('u', 2),  # embedded
            'handle_token': GLib.Variant('s', f'src_{token}')
        }
        
        result = self._portal.call_sync(
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
        
        GLib.timeout_add_seconds(15, loop.quit)
        loop.run()
        self._bus.signal_unsubscribe(sub_id)
        
        if not success:
            raise PermissionDenied("User denied source selection")
    
    def _start_capture(self) -> Tuple[int, Dict[str, Any]]:
        """Start capture and get PipeWire node"""
        loop = GLib.MainLoop()
        stream_info = None
        
        token = uuid.uuid4().hex[:8]
        options = {
            'handle_token': GLib.Variant('s', f'start_{token}')
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
            nonlocal stream_info
            error_code, results = params
            if error_code == 0:
                streams = results.get('streams', [])
                if streams:
                    stream_info = streams[0]
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
        
        if stream_info is None:
            raise CaptureError("Failed to start capture - no stream info")
        
        # Extract node ID and metadata
        if isinstance(stream_info, tuple) and len(stream_info) >= 2:
            node_id = stream_info[0]
            metadata = stream_info[1] if len(stream_info) > 1 else {}
            return node_id, metadata
        else:
            raise CaptureError(f"Unexpected stream format: {stream_info}")
    
    def _capture_frame(self, node_id: int) -> bytes:
        """Capture single frame via GStreamer"""
        pipeline_str = (
            f'pipewiresrc path={node_id} num-buffers=1 ! '
            f'videoconvert ! '
            f'video/x-raw,format=RGB ! '
            f'pngenc ! '
            f'appsink name=sink'
        )
        
        try:
            pipeline = Gst.parse_launch(pipeline_str)
            appsink = pipeline.get_by_name('sink')
            pipeline.set_state(Gst.State.PLAYING)
            
            frame_data = None
            start_time = time.time()
            
            while time.time() - start_time < 10:
                sample = appsink.emit('pull-sample')
                if sample:
                    buffer = sample.get_buffer()
                    success, mapinfo = buffer.map(Gst.MapFlags.READ)
                    if success:
                        frame_data = bytes(mapinfo.data)
                        buffer.unmap(mapinfo)
                        break
                time.sleep(0.05)
            
            pipeline.set_state(Gst.State.NULL)
            
            if frame_data is None:
                raise CaptureError("Failed to capture frame within timeout")
            
            return frame_data
            
        except Exception as e:
            raise CaptureError(f"GStreamer error: {e}") from e
