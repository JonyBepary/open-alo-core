"""
Unit tests for legacy WaylandInput and WaylandCapture modules.

Ensures backward-compatibility and full coverage for the legacy API.
"""

import json
from unittest.mock import MagicMock, call, patch

import pytest

from open_alo_core import (
    CaptureError,
    InputError,
    PermissionDenied,
    Point,
    SessionError,
    WaylandCapture,
    WaylandInput,
)
from open_alo_core.wayland.capture import CaptureResult


class TestLegacyWaylandInput:
    """WaylandInput legacy controller."""

    def test_construction_and_defaults(self, tmp_path):
        token_path = tmp_path / "legacy_tokens.json"
        ctrl = WaylandInput(token_path=token_path)
        assert ctrl._initialized is False
        assert ctrl._session_handle is None
        assert ctrl._token_path == token_path

    def test_context_manager(self):
        with WaylandInput() as ctrl:
            assert ctrl._initialized is False
        assert ctrl._session_handle is None

    def test_initialize_idempotent(self):
        ctrl = WaylandInput()
        with (
            patch.object(ctrl, "_ensure_dbus"),
            patch.object(ctrl, "_create_session") as mock_create,
        ):
            ctrl.initialize(persist_mode=2)
            ctrl.initialize(persist_mode=2)
            assert mock_create.call_count == 1
            assert ctrl._initialized is True

    def test_uninitialized_methods_raise_runtime_error(self):
        ctrl = WaylandInput()
        with pytest.raises(RuntimeError, match="Not initialized"):
            ctrl.click(Point(10, 10))
        with pytest.raises(RuntimeError, match="Not initialized"):
            ctrl.move_mouse(Point(10, 10))
        with pytest.raises(RuntimeError, match="Not initialized"):
            ctrl.type_text("test")
        with pytest.raises(RuntimeError, match="Not initialized"):
            ctrl.press_key("Return")
        with pytest.raises(RuntimeError, match="Not initialized"):
            ctrl.key_combo(["ctrl", "a"])

    def test_input_actions_happy_path(self):
        ctrl = WaylandInput()
        ctrl._initialized = True
        ctrl._session_handle = "/session/test"
        ctrl._portal = MagicMock()

        with (
            patch.object(ctrl, "_notify_pointer_motion_absolute") as mock_motion,
            patch.object(ctrl, "_notify_pointer_button") as mock_button,
            patch.object(ctrl, "_notify_keyboard_keysym") as mock_key,
        ):
            ctrl.click(Point(100, 200), button=1)
            mock_motion.assert_called_with(100, 200)
            mock_button.assert_any_call(1, pressed=True)
            mock_button.assert_any_call(1, pressed=False)

            ctrl.move_mouse(Point(300, 400))
            mock_motion.assert_called_with(300, 400)

            ctrl.press_key("Return")
            mock_key.assert_any_call("Return", pressed=True)
            mock_key.assert_any_call("Return", pressed=False)

            ctrl.type_text("Hi", interval=0.0001)
            assert mock_key.call_count >= 4

            ctrl.key_combo(["ctrl", "c"])
            assert mock_key.call_count >= 8

    def test_input_actions_wrap_exceptions(self):
        ctrl = WaylandInput()
        ctrl._initialized = True
        ctrl._session_handle = "/session/test"
        ctrl._portal = MagicMock()

        with patch.object(ctrl, "_notify_pointer_motion_absolute", side_effect=Exception("error")):
            with pytest.raises(InputError, match="Click failed"):
                ctrl.click(Point(100, 200))
            with pytest.raises(InputError, match="Mouse move failed"):
                ctrl.move_mouse(Point(100, 200))


        with patch.object(ctrl, "_notify_keyboard_keysym", side_effect=Exception("error")):
            with pytest.raises(InputError, match="Key press failed"):
                ctrl.press_key("a")
            with pytest.raises(InputError, match="Key combo failed"):
                ctrl.key_combo(["ctrl", "a"])
            with pytest.raises(InputError, match="Typing failed"):
                ctrl.type_text("a")

    def test_close_calls_portal_close(self):
        ctrl = WaylandInput()
        portal_mock = MagicMock()
        ctrl._portal = portal_mock
        ctrl._session_handle = "/session/99"
        ctrl._initialized = True

        ctrl.close()
        portal_mock.call_sync.assert_called_once()
        assert ctrl._session_handle is None
        assert ctrl._initialized is False

    def test_ensure_dbus(self):
        ctrl = WaylandInput()
        assert ctrl._bus is None
        ctrl._ensure_dbus()
        assert ctrl._bus is not None
        assert ctrl._portal is not None
        # Idempotency
        bus = ctrl._bus
        ctrl._ensure_dbus()
        assert ctrl._bus is bus

    def test_create_session_error_handling(self):
        ctrl = WaylandInput()
        ctrl._bus = MagicMock()
        ctrl._portal = MagicMock()

        with patch("open_alo_core.wayland.input.portal_request", return_value=(1, {})):
            with pytest.raises(PermissionDenied):
                ctrl._create_session(persist_mode=0)

        with patch("open_alo_core.wayland.input.portal_request", return_value=(2, {})):
            with pytest.raises(SessionError):
                ctrl._create_session(persist_mode=0)

        with patch("open_alo_core.wayland.input.portal_request", return_value=(0, None)):
            with pytest.raises(SessionError, match="No response"):
                ctrl._create_session(persist_mode=0)

    def test_select_devices_and_start_session(self):
        ctrl = WaylandInput()
        ctrl._bus = MagicMock()
        ctrl._portal = MagicMock()
        ctrl._session_handle = "/session/1"

        with patch("open_alo_core.wayland.input.portal_request", return_value=(1, {})):
            with pytest.raises(PermissionDenied):
                ctrl._select_devices(persist_mode=2)

        responses = [
            (0, {"restore_token": "token123"}),  # SelectDevices
            (0, {}),  # StartSession
        ]
        with patch("open_alo_core.wayland.input.portal_request", side_effect=responses):
            with patch.object(ctrl, "_save_token") as mock_save:
                ctrl._select_devices(persist_mode=2)
                mock_save.assert_called_once_with("token123")

        with patch("open_alo_core.wayland.input.portal_request", return_value=(1, {})):
            with pytest.raises(SessionError):
                ctrl._start_session()

        with patch("open_alo_core.wayland.input.portal_request", return_value=(0, {})):
            ctrl._start_session()

    def test_private_notify_methods(self):
        ctrl = WaylandInput()
        ctrl._portal = MagicMock()
        ctrl._session_handle = "/session/1"

        ctrl._notify_pointer_motion(50, 60)
        ctrl._notify_pointer_button(1, pressed=True)
        ctrl._notify_keyboard_keysym("Return", pressed=False)

        assert ctrl._portal.call_sync.call_count == 3
        called_methods = [c[0][0] for c in ctrl._portal.call_sync.call_args_list]
        assert called_methods == ["NotifyPointerMotion", "NotifyPointerButton", "NotifyKeyboardKeysym"]

    def test_notify_pointer_motion_absolute_paths(self):
        from open_alo_core.exceptions import InputError

        ctrl = WaylandInput()
        ctrl._portal = MagicMock()
        ctrl._session_handle = "/session/1"

        # 1. Happy path
        ctrl._notify_pointer_motion_absolute(100, 200)
        assert ctrl._portal.call_sync.call_count == 1

        # 2. Fallback
        ctrl._portal.call_sync.side_effect = [Exception("Stream unsupported"), MagicMock()]
        ctrl._notify_pointer_motion_absolute(100, 200)
        assert ctrl._portal.call_sync.call_count == 3

        # 3. Error
        ctrl._portal.call_sync.side_effect = [Exception("Fail 1"), Exception("Fail 2")]
        with pytest.raises(InputError, match="Absolute pointer motion failed on portal"):
            ctrl._notify_pointer_motion_absolute(100, 200)


    def test_token_persistence(self, tmp_path):
        token_path = tmp_path / "tokens.json"
        ctrl = WaylandInput(token_path=token_path)
        assert ctrl._load_token() is None

        ctrl._save_token("restore_xyz")
        assert ctrl._load_token() == "restore_xyz"


class TestLegacyWaylandCapture:
    """WaylandCapture legacy controller."""

    def test_construction(self):
        cap = WaylandCapture()
        assert cap._session_handle is None

    def test_context_manager(self):
        with WaylandCapture() as cap:
            assert cap._session_handle is None

    def test_capture_result_repr(self):
        res = CaptureResult(data=b"12345", source_type="monitor", size=(1920, 1080))
        assert "CaptureResult(5 bytes, monitor, (1920, 1080))" == repr(res)

    def test_ensure_dbus(self):
        cap = WaylandCapture()
        assert cap._bus is None
        cap._ensure_dbus()
        assert cap._bus is not None
        assert cap._portal is not None
        bus = cap._bus
        cap._ensure_dbus()
        assert cap._bus is bus

    def test_capture_screen_happy_path(self):
        cap = WaylandCapture()
        with (
            patch.object(cap, "_ensure_dbus"),
            patch.object(cap, "_create_session"),
            patch.object(cap, "_select_sources"),
            patch.object(cap, "_start_capture", return_value=(42, {"source_type": 1, "size": (1920, 1080)})),
            patch.object(cap, "_capture_frame", return_value=b"png_bytes"),
            patch.object(cap, "close") as mock_close,
        ):
            result = cap.capture_screen()
            assert isinstance(result, CaptureResult)
            assert result.data == b"png_bytes"
            assert result.source_type == "monitor"
            assert result.size == (1920, 1080)
            mock_close.assert_called_once()

    def test_capture_screen_error_wraps_capture_error(self):
        cap = WaylandCapture()
        with (
            patch.object(cap, "_ensure_dbus"),
            patch.object(cap, "_create_session", side_effect=Exception("Portal down")),
        ):
            with pytest.raises(CaptureError, match="Screen capture failed"):
                cap.capture_screen()

    def test_create_session_error_handling(self):
        cap = WaylandCapture()
        cap._bus = MagicMock()
        cap._portal = MagicMock()

        with patch("open_alo_core.wayland.capture.portal_request", return_value=(1, {})):
            with pytest.raises(PermissionDenied):
                cap._create_session()

        with patch("open_alo_core.wayland.capture.portal_request", return_value=(2, {})):
            with pytest.raises(CaptureError):
                cap._create_session()

        with patch("open_alo_core.wayland.capture.portal_request", return_value=(0, None)):
            with pytest.raises(CaptureError, match="No response"):
                cap._create_session()

    def test_select_sources_error_handling(self):
        cap = WaylandCapture()
        cap._bus = MagicMock()
        cap._portal = MagicMock()
        cap._session_handle = "/session/1"

        with patch("open_alo_core.wayland.capture.portal_request", return_value=(1, {})):
            with pytest.raises(PermissionDenied):
                cap._select_sources()

        with patch("open_alo_core.wayland.capture.portal_request", return_value=(0, {})):
            cap._select_sources()

    def test_start_capture_error_handling(self):
        cap = WaylandCapture()
        cap._bus = MagicMock()
        cap._portal = MagicMock()

        with patch("open_alo_core.wayland.capture.portal_request", return_value=(0, {"streams": []})):
            with pytest.raises(CaptureError, match="no streams"):
                cap._start_capture()

        with patch("open_alo_core.wayland.capture.portal_request", return_value=(0, {"streams": ["bad_format"]})):
            with pytest.raises(CaptureError, match="Unexpected stream format"):
                cap._start_capture()

    def test_capture_frame_happy_path(self):
        from gi.repository import Gst

        cap = WaylandCapture()
        mock_pipeline = MagicMock()
        mock_appsink = MagicMock()
        mock_sample = MagicMock()
        mock_buffer = MagicMock()
        mock_mapinfo = MagicMock()
        mock_mapinfo.data = b"image_bytes"

        mock_buffer.map.return_value = (True, mock_mapinfo)
        mock_sample.get_buffer.return_value = mock_buffer
        mock_appsink.emit.return_value = mock_sample
        mock_pipeline.get_by_name.return_value = mock_appsink

        with patch("open_alo_core.wayland.capture.Gst.parse_launch", return_value=mock_pipeline):
            frame = cap._capture_frame(42)
            assert frame == b"image_bytes"
            mock_pipeline.set_state.assert_called_with(Gst.State.NULL)
            mock_buffer.unmap.assert_called_once_with(mock_mapinfo)

