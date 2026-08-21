"""
Mock-based unit tests for UnifiedRemoteDesktop.

These tests verify construction, initialization flow, input actions,
screen capture, and error handling without requiring a Wayland session
or portal interaction.
All PyGObject imports are mocked via conftest.py.
"""

import json
from unittest.mock import ANY, MagicMock, call, patch

import pytest

from open_alo_core import (
    CaptureError,
    InputError,
    PermissionDenied,
    Point,
    SessionError,
    UnifiedRemoteDesktop,
    create_unified_desktop,
)


class TestUnifiedRemoteDesktopConstruction:
    """UnifiedRemoteDesktop.__init__() — construction and defaults."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop

    def test_default_construction(self):
        remote = self.cls()
        assert remote._initialized is False
        assert remote._session_handle is None
        assert remote._pipewire_node is None
        assert remote._pipeline is None
        assert remote._appsink is None
        assert remote._portal is None
        assert "unified_token.json" in str(remote._token_path)

    def test_custom_token_path(self, tmp_path):
        token_path = tmp_path / "custom_token.json"
        remote = self.cls(token_path=token_path)
        assert remote._token_path == token_path

    def test_context_manager(self):
        with self.cls() as remote:
            assert remote._initialized is False
        assert remote._initialized is False

    def test_context_manager_closes_on_exit(self):
        close_mock = MagicMock()
        with patch.object(self.cls, "close", close_mock):
            with self.cls() as remote:
                pass
        close_mock.assert_called_once()


class TestUnifiedRemoteDesktopInitialize:
    """UnifiedRemoteDesktop.initialize() — session creation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop

    def test_initialize_returns_true(self):
        with patch.object(self.cls, "_create_session", MagicMock()) as mock_create:
            remote = self.cls()
            result = remote.initialize(persist_mode=2, enable_capture=True)
            assert result is True
            assert remote._initialized is True
            mock_create.assert_called_once_with(2, True)

    def test_initialize_idempotent(self):
        with patch.object(self.cls, "_create_session", MagicMock()) as mock_create:
            remote = self.cls()
            remote.initialize()
            remote.initialize()  # Second call should be no-op
            assert mock_create.call_count == 1

    def test_initialize_calls_ensure_dbus(self):
        remote = self.cls()
        with patch.object(remote, "_ensure_dbus", MagicMock()) as mock_dbus:
            with patch.object(remote, "_create_session", MagicMock()):
                remote.initialize()
                mock_dbus.assert_called_once()

    def test_initialize_without_capture(self):
        with patch.object(self.cls, "_create_session", MagicMock()) as mock_create:
            remote = self.cls()
            remote.initialize(persist_mode=0, enable_capture=False)
            mock_create.assert_called_once_with(0, False)


class TestUnifiedRemoteDesktopClose:
    """UnifiedRemoteDesktop.close() — resource cleanup."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop

    def test_close_clears_state(self):
        remote = self.cls()
        remote._session_handle = "/session/1"
        remote._initialized = True
        remote.close()
        assert remote._session_handle is None
        assert remote._initialized is False
        assert remote._pipewire_node is None

    def test_close_stops_pipeline(self):
        from gi.repository import Gst

        remote = self.cls()
        pipeline_mock = MagicMock()
        remote._pipeline = pipeline_mock
        remote.close()
        pipeline_mock.set_state.assert_called_once_with(Gst.State.NULL)
        assert remote._pipeline is None
        assert remote._appsink is None

    def test_close_calls_portal_close(self):
        remote = self.cls()
        portal_mock = MagicMock()
        remote._portal = portal_mock
        remote._session_handle = "/session/123"
        remote._initialized = True

        remote.close()
        portal_mock.call_sync.assert_called_once()
        args = portal_mock.call_sync.call_args[0]
        assert args[0] == "Close"
        assert remote._session_handle is None


class TestUnifiedRemoteDesktopInput:
    """UnifiedRemoteDesktop input methods — happy path and error handling."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop
        self.Point = Point

    def _make_initialized(self):
        desktop = self.cls()
        desktop._initialized = True
        desktop._session_handle = "/test/session"
        desktop._portal = MagicMock()
        desktop._pause = 0.0001
        return desktop

    def test_click_raises_if_not_initialized(self):
        remote = self.cls()
        with pytest.raises(RuntimeError, match="Not initialized"):
            remote.click(self.Point(100, 100))

    def test_click_happy_path(self):
        desktop = self._make_initialized()
        with (
            patch.object(desktop, "_notify_pointer_motion_absolute") as mock_motion,
            patch.object(desktop, "_notify_pointer_button") as mock_button,
        ):
            desktop.click(self.Point(150, 250), button=1)
            mock_motion.assert_called_once_with(150, 250)
            assert mock_button.call_args_list == [
                call(1, pressed=True),
                call(1, pressed=False),
            ]

    def test_click_wraps_exception(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_pointer_motion_absolute", side_effect=Exception("D-Bus down")):
            with pytest.raises(InputError, match="Click failed"):
                desktop.click(self.Point(100, 100))

    def test_move_mouse_raises_if_not_initialized(self):
        remote = self.cls()
        with pytest.raises(RuntimeError, match="Not initialized"):
            remote.move_mouse(self.Point(100, 100))

    def test_move_mouse_happy_path(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_pointer_motion_absolute") as mock_motion:
            desktop.move_mouse(self.Point(300, 400))
            mock_motion.assert_called_once_with(300, 400)

    def test_move_mouse_wraps_exception(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_pointer_motion_absolute", side_effect=Exception("error")):
            with pytest.raises(InputError, match="Mouse move failed"):
                desktop.move_mouse(self.Point(10, 20))

    def test_notify_pointer_motion_absolute_happy_path(self):
        desktop = self._make_initialized()
        desktop._pipewire_node = 42
        desktop._notify_pointer_motion_absolute(100, 200)
        desktop._portal.call_sync.assert_called_once()
        method, variant = desktop._portal.call_sync.call_args[0][:2]
        assert method == "NotifyPointerMotionAbsolute"

    def test_notify_pointer_motion_absolute_fallback_on_error(self):
        desktop = self._make_initialized()
        # First call fails with stream ID, second succeeds without stream ID
        desktop._portal.call_sync.side_effect = [Exception("Stream unsupported"), MagicMock()]
        desktop._notify_pointer_motion_absolute(100, 200)
        assert desktop._portal.call_sync.call_count == 2

    def test_notify_pointer_motion_absolute_raises_input_error_when_both_fail(self):
        from open_alo_core.exceptions import InputError

        desktop = self._make_initialized()
        desktop._portal.call_sync.side_effect = [Exception("Failed 1"), Exception("Failed 2")]
        with pytest.raises(InputError, match="Absolute pointer motion failed on portal"):
            desktop._notify_pointer_motion_absolute(100, 200)




    def test_type_text_raises_if_not_initialized(self):
        remote = self.cls()
        with pytest.raises(RuntimeError, match="Not initialized"):
            remote.type_text("hello")

    def test_type_text_happy_path(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_keyboard_keysym") as mock_key:
            desktop.type_text("Hi!", interval=0.0001)
            assert mock_key.call_count == 6  # 3 chars * 2 (press + release)
            mock_key.assert_has_calls(
                [
                    call("H", pressed=True),
                    call("H", pressed=False),
                    call("i", pressed=True),
                    call("i", pressed=False),
                    call("!", pressed=True),
                    call("!", pressed=False),
                ]
            )

    def test_type_text_wraps_exception(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_keyboard_keysym", side_effect=Exception("type error")):
            with pytest.raises(InputError, match="Typing failed"):
                desktop.type_text("a")

    def test_press_key_raises_if_not_initialized(self):

        remote = self.cls()
        with pytest.raises(RuntimeError, match="Not initialized"):
            remote.press_key("Return")

    def test_press_key_happy_path(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_keyboard_keysym") as mock_key:
            desktop.press_key("enter")  # Alias normalized to Return
            mock_key.assert_has_calls(
                [
                    call("Return", pressed=True),
                    call("Return", pressed=False),
                ]
            )

    def test_press_key_wraps_exception(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_keyboard_keysym", side_effect=Exception("key error")):
            with pytest.raises(InputError, match="Key press failed"):
                desktop.press_key("a")

    def test_key_combo_raises_if_not_initialized(self):
        remote = self.cls()
        with pytest.raises(RuntimeError, match="Not initialized"):
            remote.key_combo(["ctrl", "a"])

    def test_key_combo_press_forward_release_reverse(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_keyboard_keysym") as mock_key:
            desktop.key_combo(["ctrl", "shift", "t"])
            mock_key.assert_has_calls(
                [
                    call("Control", pressed=True),
                    call("Shift", pressed=True),
                    call("t", pressed=True),
                    call("t", pressed=False),
                    call("Shift", pressed=False),
                    call("Control", pressed=False),
                ]
            )

    def test_key_combo_wraps_exception(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_keyboard_keysym", side_effect=Exception("combo error")):
            with pytest.raises(InputError, match="Key combo failed"):
                desktop.key_combo(["ctrl", "c"])


class TestUnifiedRemoteDesktopCapture:
    """UnifiedRemoteDesktop capture methods — screenshot, get_frame, get_screen_size."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop

    def _make_initialized(self):
        from gi.repository import Gst

        desktop = self.cls()
        desktop._initialized = True
        desktop._session_handle = "/test/session"
        desktop._pipewire_node = 42
        desktop._pipeline = MagicMock()
        desktop._pipeline.get_state.return_value = (
            Gst.StateChangeReturn.SUCCESS,
            Gst.State.PLAYING,
            0,
        )
        desktop._appsink = MagicMock()
        return desktop


    def test_capture_screenshot_raises_if_not_initialized(self):
        remote = self.cls()
        with pytest.raises(RuntimeError, match="Not initialized"):
            remote.capture_screenshot()

    def test_capture_screenshot_raises_if_no_pipewire(self):
        remote = self.cls()
        remote._initialized = True
        with pytest.raises(RuntimeError, match="capture not enabled"):
            remote.capture_screenshot()

    def test_capture_screenshot_happy_path(self):
        desktop = self._make_initialized()
        mock_sample = MagicMock()
        mock_buffer = MagicMock()
        mock_map_info = MagicMock()
        mock_map_info.data = b"\x89PNG\r\n\x1a\nfake_image_data"
        mock_buffer.map.return_value = (True, mock_map_info)
        mock_sample.get_buffer.return_value = mock_buffer
        desktop._appsink.emit.return_value = mock_sample

        png = desktop.capture_screenshot()
        assert png == b"\x89PNG\r\n\x1a\nfake_image_data"
        mock_buffer.unmap.assert_called_once_with(mock_map_info)

    def test_capture_screenshot_no_sample_raises_capture_error(self):
        desktop = self._make_initialized()
        desktop._appsink.emit.return_value = None
        with pytest.raises(CaptureError, match="No sample available"):
            desktop.capture_screenshot()

    def test_capture_screenshot_no_buffer_raises_capture_error(self):
        desktop = self._make_initialized()
        mock_sample = MagicMock()
        mock_sample.get_buffer.return_value = None
        desktop._appsink.emit.return_value = mock_sample
        with pytest.raises(CaptureError, match="No buffer in sample"):
            desktop.capture_screenshot()

    def test_capture_screenshot_map_failed_raises_capture_error(self):
        desktop = self._make_initialized()
        mock_sample = MagicMock()
        mock_buffer = MagicMock()
        mock_buffer.map.return_value = (False, None)
        mock_sample.get_buffer.return_value = mock_buffer
        desktop._appsink.emit.return_value = mock_sample
        with pytest.raises(CaptureError, match="Failed to map buffer"):
            desktop.capture_screenshot()

    def test_get_frame_returns_none_if_not_initialized(self):
        remote = self.cls()
        assert remote.get_frame() is None

    def test_get_frame_happy_path(self):
        desktop = self._make_initialized()
        mock_sample = MagicMock()
        mock_buffer = MagicMock()
        mock_map_info = MagicMock()
        mock_map_info.data = b"frame_bytes"
        mock_buffer.map.return_value = (True, mock_map_info)
        mock_sample.get_buffer.return_value = mock_buffer
        desktop._appsink.emit.return_value = mock_sample

        frame = desktop.get_frame()
        assert frame == b"frame_bytes"
        mock_buffer.unmap.assert_called_once_with(mock_map_info)

    def test_get_frame_returns_none_on_no_sample(self):
        desktop = self._make_initialized()
        desktop._appsink.emit.return_value = None
        assert desktop.get_frame() is None

    def test_get_screen_size_returns_none_without_pipeline(self):
        remote = self.cls()
        assert remote.get_screen_size() is None

    def test_get_screen_size_happy_path(self):
        desktop = self._make_initialized()
        mock_pad = MagicMock()
        mock_caps = MagicMock()
        mock_struct = MagicMock()
        mock_struct.get_int.side_effect = lambda field: (True, 1920 if field == "width" else 1080)
        mock_caps.get_structure.return_value = mock_struct
        mock_pad.get_current_caps.return_value = mock_caps
        desktop._appsink.get_static_pad.return_value = mock_pad

        size = desktop.get_screen_size()
        assert size == (1920, 1080)


class TestUnifiedRemoteDesktopEnsurePipeline:
    """UnifiedRemoteDesktop._ensure_pipeline() — pipeline lifecycle."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop

    def test_raises_if_no_pipewire_node(self):
        remote = self.cls()
        with pytest.raises(CaptureError, match="PipeWire node"):
            remote._ensure_pipeline()

    def test_creates_pipeline_if_not_running(self):
        remote = self.cls()
        remote._pipewire_node = 42
        remote._ensure_pipeline()
        assert remote._pipeline is not None
        assert remote._appsink is not None

    def test_reuses_running_pipeline(self):
        """If pipeline is already PLAYING, should not create a new one."""
        from gi.repository import Gst

        remote = self.cls()
        remote._pipewire_node = 42
        old_pipeline = MagicMock()
        remote._pipeline = old_pipeline
        remote._appsink = MagicMock()

        old_pipeline.get_state.return_value = (
            Gst.StateChangeReturn.SUCCESS,
            Gst.State.PLAYING,
        )

        remote._ensure_pipeline()
        assert remote._pipeline is old_pipeline


class TestUnifiedRemoteDesktopSessionCreation:
    """Session creation flow and error handling."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop

    def test_create_session_handles_error_code_1(self):
        """Error code 1 = user denied permission."""
        remote = self.cls()
        remote._bus = MagicMock()
        remote._portal = MagicMock()
        remote._screencast_portal = MagicMock()

        with patch("open_alo_core.wayland.unified.portal_request", return_value=(1, {})):
            with pytest.raises(PermissionDenied, match="User denied permission"):
                remote._create_session(persist_mode=2, enable_capture=True)

    def test_create_session_handles_portal_timeout(self):
        """None results = timeout error."""
        remote = self.cls()
        remote._bus = MagicMock()
        remote._portal = MagicMock()
        remote._screencast_portal = MagicMock()

        with patch("open_alo_core.wayland.unified.portal_request", return_value=(0, None)):
            with pytest.raises(SessionError, match="No response from portal"):
                remote._create_session(persist_mode=2, enable_capture=True)

    def test_create_session_handles_generic_error_code(self):
        """Other error codes raise SessionError."""
        remote = self.cls()
        remote._bus = MagicMock()
        remote._portal = MagicMock()
        remote._screencast_portal = MagicMock()

        with patch("open_alo_core.wayland.unified.portal_request", return_value=(2, {})):
            with pytest.raises(SessionError, match="Failed to create session"):
                remote._create_session(persist_mode=2, enable_capture=True)

    def test_create_session_full_flow_with_capture(self):
        """Full create_session flow with select_devices, select_sources, start."""
        remote = self.cls()
        remote._bus = MagicMock()
        remote._portal = MagicMock()
        remote._screencast_portal = MagicMock()

        responses = [
            (0, {"session_handle": "/session/100"}),  # CreateSession
            (0, {"restore_token": "dev_restore_123"}),  # SelectDevices
            (0, {}),  # SelectSources
            (0, {"streams": [(123, {"id": 42})]}),  # Start
        ]

        with patch("open_alo_core.wayland.unified.portal_request", side_effect=responses):
            with patch.object(remote, "_save_token") as mock_save:
                remote._create_session(persist_mode=2, enable_capture=True)
                assert remote._session_handle == "/session/100"
                mock_save.assert_called_once_with("dev_restore_123")


class TestUnifiedRemoteDesktopTokenHandling:
    """Token load and save persistence."""

    def test_save_and_load_token(self, tmp_path):
        token_path = tmp_path / "token.json"
        remote = UnifiedRemoteDesktop(token_path=token_path)

        assert remote._load_token() is None

        remote._save_token("test_restore_token_xyz")
        assert token_path.exists()
        data = json.loads(token_path.read_text())
        assert data.get("restore_token") == "test_restore_token_xyz"

        assert remote._load_token() == "test_restore_token_xyz"

    def test_load_token_handles_corrupt_file(self, tmp_path):
        token_path = tmp_path / "token.json"
        token_path.write_text("invalid json")
        remote = UnifiedRemoteDesktop(token_path=token_path)
        assert remote._load_token() is None


class TestUnifiedRemoteDesktopNotifications:
    """Test private D-Bus notification helper methods."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop

    def test_notify_pointer_motion(self):
        remote = self.cls()
        remote._session_handle = "/session/123"
        remote._portal = MagicMock()

        remote._notify_pointer_motion(100, 200)
        remote._portal.call_sync.assert_called_once()
        args = remote._portal.call_sync.call_args[0]
        assert args[0] == "NotifyPointerMotion"

    def test_notify_pointer_button(self):
        remote = self.cls()
        remote._session_handle = "/session/123"
        remote._portal = MagicMock()

        remote._notify_pointer_button(1, pressed=True)
        remote._portal.call_sync.assert_called_once()
        args = remote._portal.call_sync.call_args[0]
        assert args[0] == "NotifyPointerButton"

    def test_notify_keyboard_keysym(self):
        remote = self.cls()
        remote._session_handle = "/session/123"
        remote._portal = MagicMock()

        remote._notify_keyboard_keysym("Return", pressed=True)
        remote._portal.call_sync.assert_called_once()
        args = remote._portal.call_sync.call_args[0]
        assert args[0] == "NotifyKeyboardKeysym"


class TestUnifiedRemoteDesktopScroll:

    """UnifiedRemoteDesktop scroll methods — scroll, hscroll, smooth_scroll."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from gi.repository import GLib

        self.cls = UnifiedRemoteDesktop
        self.GLib = GLib

    def _make_initialized(self):
        desktop = self.cls()
        desktop._initialized = True
        desktop._session_handle = "/test/session"
        desktop._portal = MagicMock()
        desktop._pause = 0.001
        return desktop

    def test_scroll_vertical_down(self):
        self.GLib.Variant.reset_mock()
        desktop = self._make_initialized()
        desktop.scroll(-3)
        args = desktop._portal.call_sync.call_args[0]
        assert args[0] == "NotifyPointerAxisDiscrete"
        self.GLib.Variant.assert_called_with("(oa{sv}ui)", ("/test/session", {}, 0, -3))

    def test_scroll_vertical_up(self):
        self.GLib.Variant.reset_mock()
        desktop = self._make_initialized()
        desktop.scroll(5)
        args = desktop._portal.call_sync.call_args[0]
        assert args[0] == "NotifyPointerAxisDiscrete"
        self.GLib.Variant.assert_called_with("(oa{sv}ui)", ("/test/session", {}, 0, 5))

    def test_scroll_with_coords(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_pointer_motion") as mock_motion:
            desktop.scroll(5, x=100, y=200)
            mock_motion.assert_called_once_with(100, 200)
            args = desktop._portal.call_sync.call_args[0]
            assert args[0] == "NotifyPointerAxisDiscrete"

    def test_scroll_not_initialized(self):
        desktop = self.cls()
        with pytest.raises(RuntimeError, match="Not initialized"):
            desktop.scroll(1)

    def test_hscroll_right(self):
        self.GLib.Variant.reset_mock()
        desktop = self._make_initialized()
        desktop.hscroll(3)
        args = desktop._portal.call_sync.call_args[0]
        assert args[0] == "NotifyPointerAxisDiscrete"
        self.GLib.Variant.assert_called_with("(oa{sv}ui)", ("/test/session", {}, 1, 3))

    def test_hscroll_left(self):
        self.GLib.Variant.reset_mock()
        desktop = self._make_initialized()
        desktop.hscroll(-2)
        args = desktop._portal.call_sync.call_args[0]
        assert args[0] == "NotifyPointerAxisDiscrete"
        self.GLib.Variant.assert_called_with("(oa{sv}ui)", ("/test/session", {}, 1, -2))

    def test_smooth_scroll(self):
        self.GLib.Variant.reset_mock()
        desktop = self._make_initialized()
        desktop.smooth_scroll(dx=0, dy=-50)
        args = desktop._portal.call_sync.call_args[0]
        assert args[0] == "NotifyPointerAxis"
        self.GLib.Variant.assert_called_with(
            "(oa{sv}dd)", ("/test/session", {}, 0.0, -50.0)
        )

    def test_scroll_error_wraps_input_error(self):
        desktop = self._make_initialized()
        desktop._portal.call_sync.side_effect = Exception("dbus down")
        with pytest.raises(InputError, match="Scroll failed"):
            desktop.scroll(1)

    def test_hscroll_with_coords(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_pointer_motion") as mock_motion:
            desktop.hscroll(3, x=50, y=60)
            mock_motion.assert_called_once_with(50, 60)

    def test_hscroll_error_wraps_input_error(self):
        desktop = self._make_initialized()
        desktop._portal.call_sync.side_effect = Exception("dbus down")
        with pytest.raises(InputError, match="Horizontal scroll failed"):
            desktop.hscroll(1)

    def test_smooth_scroll_error_wraps_input_error(self):
        desktop = self._make_initialized()
        desktop._portal.call_sync.side_effect = Exception("dbus down")
        with pytest.raises(InputError, match="Smooth scroll failed"):
            desktop.smooth_scroll(dx=10, dy=10)


class TestUnifiedRemoteDesktopDrag:
    """UnifiedRemoteDesktop drag methods — drag, swipe."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop
        self.Point = Point

    def _make_initialized(self):
        desktop = self.cls()
        desktop._initialized = True
        desktop._session_handle = "/test/session"
        desktop._portal = MagicMock()
        desktop._pause = 0.001
        return desktop

    def test_drag(self):
        desktop = self._make_initialized()
        with (
            patch.object(desktop, "_notify_pointer_motion") as mock_motion,
            patch.object(desktop, "_notify_pointer_button") as mock_button,
        ):
            desktop.drag(self.Point(100, 100), self.Point(200, 200))
            mock_motion.assert_any_call(100, 100)
            mock_motion.assert_any_call(200, 200)
            mock_button.assert_any_call(1, pressed=True)
            mock_button.assert_any_call(1, pressed=False)

    def test_drag_with_duration(self):
        desktop = self._make_initialized()
        with (
            patch.object(desktop, "_notify_pointer_motion") as mock_motion,
            patch.object(desktop, "_notify_pointer_button") as mock_button,
        ):
            desktop.drag(self.Point(0, 0), self.Point(100, 100), duration=0.1)
            assert mock_motion.call_count >= 5
            mock_button.assert_any_call(1, pressed=True)
            mock_button.assert_any_call(1, pressed=False)


    def test_drag_right_button(self):
        desktop = self._make_initialized()
        with (
            patch.object(desktop, "_notify_pointer_motion"),
            patch.object(desktop, "_notify_pointer_button") as mock_button,
        ):
            desktop.drag(self.Point(100, 100), self.Point(200, 200), button=3)
            mock_button.assert_any_call(3, pressed=True)
            mock_button.assert_any_call(3, pressed=False)

    def test_drag_releases_on_error(self):
        desktop = self._make_initialized()
        motion_calls = [None, Exception("drag motion error")]
        with (
            patch.object(desktop, "_notify_pointer_motion", side_effect=motion_calls),
            patch.object(desktop, "_notify_pointer_button") as mock_button,
        ):
            with pytest.raises(InputError, match="Drag failed"):
                desktop.drag(self.Point(0, 0), self.Point(100, 100))
            mock_button.assert_any_call(1, pressed=True)
            mock_button.assert_any_call(1, pressed=False)

    def test_drag_not_initialized(self):
        desktop = self.cls()
        with pytest.raises(RuntimeError, match="Not initialized"):
            desktop.drag(self.Point(0, 0), self.Point(100, 100))

    def test_swipe(self):
        desktop = self._make_initialized()
        with (
            patch.object(desktop, "_notify_pointer_motion") as mock_motion,
            patch.object(desktop, "_notify_pointer_button") as mock_button,
        ):
            desktop.swipe(self.Point(0, 0), self.Point(100, 100), steps=3)
            assert mock_motion.call_count == 1 + 3
            mock_motion.assert_any_call(0, 0)
            mock_motion.assert_any_call(100, 100)
            mock_button.assert_any_call(1, pressed=True)
            mock_button.assert_any_call(1, pressed=False)

    def test_swipe_releases_on_error(self):
        desktop = self._make_initialized()
        motion_calls = [None, None, Exception("swipe error")]
        with (
            patch.object(desktop, "_notify_pointer_motion", side_effect=motion_calls),
            patch.object(desktop, "_notify_pointer_button") as mock_button,
        ):
            with pytest.raises(InputError, match="Swipe failed"):
                desktop.swipe(self.Point(0, 0), self.Point(100, 100), steps=3)
            mock_button.assert_any_call(1, pressed=True)
            mock_button.assert_any_call(1, pressed=False)


class TestUnifiedRemoteDesktopConvenience:
    """UnifiedRemoteDesktop convenience methods."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop
        self.Point = Point

    def _make_initialized(self):
        desktop = self.cls()
        desktop._initialized = True
        desktop._session_handle = "/test/session"
        desktop._portal = MagicMock()
        desktop._pause = 0.001
        return desktop

    def test_hold_key(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "_notify_keyboard_keysym") as mock_keysym:
            with desktop.hold_key("shift"):  # Case-insensitive normalization
                mock_keysym.assert_called_with("Shift", pressed=True)
            mock_keysym.assert_called_with("Shift", pressed=False)

    def test_hold_key_not_initialized(self):
        desktop = self.cls()
        with pytest.raises(RuntimeError, match="Not initialized"):
            with desktop.hold_key("Shift"):
                pass

    def test_double_click(self):
        desktop = self._make_initialized()
        with patch.object(desktop, "click") as mock_click:
            desktop.double_click(self.Point(100, 200))
            assert mock_click.call_count == 2
            mock_click.assert_has_calls(
                [
                    call(self.Point(100, 200), 1),
                    call(self.Point(100, 200), 1),
                ]
            )

    def test_move_mouse_relative(self):
        from gi.repository import GLib

        desktop = self._make_initialized()
        GLib.Variant.reset_mock()
        desktop.move_mouse_relative(50, -25)
        args = desktop._portal.call_sync.call_args[0]
        assert args[0] == "NotifyPointerMotion"
        GLib.Variant.assert_called_with(
            "(oa{sv}dd)", ("/test/session", {}, 50.0, -25.0)
        )

    def test_move_mouse_relative_error_wraps_input_error(self):
        desktop = self._make_initialized()
        desktop._portal.call_sync.side_effect = Exception("dbus down")
        with pytest.raises(InputError, match="Relative move failed"):
            desktop.move_mouse_relative(10, 10)

    def test_ensure_dbus(self):
        remote = self.cls()
        assert remote._bus is None
        remote._ensure_dbus()
        assert remote._bus is not None
        assert remote._portal is not None
        bus = remote._bus
        remote._ensure_dbus()
        assert remote._bus is bus

    def test_press_keys(self):

        desktop = self._make_initialized()
        with patch.object(desktop, "press_key") as mock_press:
            desktop.press_keys(["a", "b", "c"])
            assert mock_press.call_count == 3
            mock_press.assert_has_calls(
                [
                    call("a"),
                    call("b"),
                    call("c"),
                ]
            )

    def test_create_unified_desktop_convenience_function(self):
        with patch.object(UnifiedRemoteDesktop, "initialize") as mock_init:
            desktop = create_unified_desktop(persist_mode=1, enable_capture=False)
            assert isinstance(desktop, UnifiedRemoteDesktop)
            mock_init.assert_called_once_with(persist_mode=1, enable_capture=False)


class TestUnifiedRemoteDesktopConfig:
    """UnifiedRemoteDesktop configuration properties — pause, fail_safe, touch_mode."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cls = UnifiedRemoteDesktop

    def test_pause_default(self):
        desktop = self.cls()
        assert desktop.pause == 0.05

    def test_pause_setter(self):
        desktop = self.cls()
        desktop.pause = 0.1
        assert desktop.pause == 0.1

    def test_pause_clamps_negative(self):
        desktop = self.cls()
        desktop.pause = -1
        assert desktop.pause == 0.0

    def test_fail_safe_default(self):
        desktop = self.cls()
        assert desktop.fail_safe is False

    def test_fail_safe_setter(self):
        desktop = self.cls()
        desktop.fail_safe = True
        assert desktop.fail_safe is True

    def test_touch_mode_property(self):
        desktop = self.cls()
        assert desktop.touch_mode is False
        desktop.touch_mode = True
        assert desktop.touch_mode is True
