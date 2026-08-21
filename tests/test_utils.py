"""
Unit tests for open_alo_core utility functions.

Uses environment variable manipulation to test session detection.
Other utilities (is_portal_available, is_pipewire_available) test
basic error handling paths via mocked imports.
"""

import os
from unittest.mock import patch

import pytest


class TestDetectSessionType:
    """detect_session_type() — detects Wayland vs X11."""

    def test_wayland(self):
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}, clear=True):
            from open_alo_core import detect_session_type

            assert detect_session_type() == "wayland"

    def test_x11(self):
        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
            from open_alo_core import detect_session_type

            assert detect_session_type() == "x11"

    def test_unknown(self):
        with patch.dict(os.environ, {}, clear=True):
            from open_alo_core import detect_session_type

            assert detect_session_type() == "unknown"

    def test_wayland_takes_priority(self):
        """WAYLAND_DISPLAY should take priority over DISPLAY."""
        with patch.dict(
            os.environ,
            {"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"},
            clear=True,
        ):
            from open_alo_core import detect_session_type

            assert detect_session_type() == "wayland"


class TestIsWayland:
    """is_wayland() — boolean check for Wayland session."""

    def test_true(self):
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}, clear=True):
            from open_alo_core import is_wayland

            assert is_wayland() is True

    def test_false(self):
        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
            from open_alo_core import is_wayland

            assert is_wayland() is False

    def test_no_display(self):
        with patch.dict(os.environ, {}, clear=True):
            from open_alo_core import is_wayland

            assert is_wayland() is False


class TestIsPortalAvailable:
    """is_portal_available() — lightweight D-Bus name check."""

    def test_available(self):
        from unittest.mock import MagicMock
        from gi.repository import Gio
        from open_alo_core import is_portal_available

        mock_bus = MagicMock()
        mock_result = MagicMock()
        mock_result.get_child_value.return_value.get_boolean.return_value = True
        mock_bus.call_sync.return_value = mock_result

        with patch.object(Gio, "bus_get_sync", return_value=mock_bus):
            assert is_portal_available() is True
            mock_bus.call_sync.assert_called_once()
            args = mock_bus.call_sync.call_args[0]
            assert args[0] == "org.freedesktop.DBus"
            assert args[3] == "NameHasOwner"

    def test_not_available(self):
        from unittest.mock import MagicMock
        from gi.repository import Gio
        from open_alo_core import is_portal_available

        mock_bus = MagicMock()
        mock_result = MagicMock()
        mock_result.get_child_value.return_value.get_boolean.return_value = False
        mock_bus.call_sync.return_value = mock_result

        with patch.object(Gio, "bus_get_sync", return_value=mock_bus):
            assert is_portal_available() is False

    def test_result_none(self):
        from unittest.mock import MagicMock
        from gi.repository import Gio
        from open_alo_core import is_portal_available

        mock_bus = MagicMock()
        mock_bus.call_sync.return_value = None

        with patch.object(Gio, "bus_get_sync", return_value=mock_bus):
            assert is_portal_available() is False

    def test_exception_handling(self):
        from gi.repository import Gio
        from open_alo_core import is_portal_available

        with patch.object(Gio, "bus_get_sync", side_effect=Exception("D-Bus connection error")):
            assert is_portal_available() is False



class TestIsPipewireAvailable:
    """is_pipewire_available() — checks pw-cli."""

    def test_available(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            from open_alo_core import is_pipewire_available

            assert is_pipewire_available() is True

    def test_not_available(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            from open_alo_core import is_pipewire_available

            assert is_pipewire_available() is False

    def test_exception_handling(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("pw-cli not found")):
            from open_alo_core import is_pipewire_available

            assert is_pipewire_available() is False


class TestGetMonotonicNs:
    """get_monotonic_ns() — nanosecond monotonic timestamp helper."""

    def test_returns_int_from_glib(self):
        from open_alo_core import get_monotonic_ns

        ts = get_monotonic_ns()
        assert isinstance(ts, int)
        assert ts > 0

    def test_fallback_to_time_monotonic(self):
        import sys
        from open_alo_core.utils import get_monotonic_ns

        with patch.dict(sys.modules, {"gi": None}):
            ts = get_monotonic_ns()
            assert isinstance(ts, int)
            assert ts > 0


class TestSanitizeRect:
    """sanitize_rect() — filters sentinel values and bounds checking."""

    def test_sentinel_int_min_rejected(self):
        from open_alo_core import Rect, sanitize_rect

        # Sentinel: -2147483648
        r1 = Rect(-2147483648, -2147483648, 1, 1)
        assert sanitize_rect(r1) is None

        r2 = Rect(-2147483648, 100, 50, 50)
        assert sanitize_rect(r2) is None

        r3 = Rect(100, -2147483648, 50, 50)
        assert sanitize_rect(r3) is None

    def test_non_positive_dimensions_rejected(self):
        from open_alo_core import Rect, sanitize_rect

        assert sanitize_rect(Rect(10, 10, 0, 0)) is None
        assert sanitize_rect(Rect(10, 10, 1, 1)) is None
        assert sanitize_rect(Rect(10, 10, 100, 1)) is None
        assert sanitize_rect(Rect(10, 10, 1, 100)) is None
        assert sanitize_rect(Rect(10, 10, -5, 20)) is None

    def test_valid_rect_without_screen_size(self):
        from open_alo_core import Rect, sanitize_rect

        r = Rect(100, 200, 300, 400)
        res = sanitize_rect(r)
        assert res == r

    def test_out_of_bounds_with_screen_size(self):
        from open_alo_core import Rect, sanitize_rect

        screen = (1920, 1080)
        # Completely to the right
        assert sanitize_rect(Rect(1920, 100, 50, 50), screen_size=screen) is None
        # Completely below
        assert sanitize_rect(Rect(100, 1080, 50, 50), screen_size=screen) is None
        # Completely to the left
        assert sanitize_rect(Rect(-100, 100, 50, 50), screen_size=screen) is None
        # Completely above
        assert sanitize_rect(Rect(100, -100, 50, 50), screen_size=screen) is None
        # Invalid screen size
        assert sanitize_rect(Rect(10, 10, 50, 50), screen_size=(0, 0)) is None

    def test_partially_out_of_bounds_clamped(self):
        from open_alo_core import Rect, sanitize_rect

        screen = (1920, 1080)
        # Partially left: x=-10, w=50 -> clamped to x=0, w=40
        r_left = Rect(-10, 100, 50, 50)
        sanitized_left = sanitize_rect(r_left, screen_size=screen)
        assert sanitized_left == Rect(0, 100, 40, 50)

        # Partially right: x=1900, w=50 -> clamped to x=1900, w=20
        r_right = Rect(1900, 100, 50, 50)
        sanitized_right = sanitize_rect(r_right, screen_size=screen)
        assert sanitized_right == Rect(1900, 100, 20, 50)

        # Partially top: y=-20, h=60 -> clamped to y=0, h=40
        r_top = Rect(100, -20, 50, 60)
        sanitized_top = sanitize_rect(r_top, screen_size=screen)
        assert sanitized_top == Rect(100, 0, 50, 40)

        # Partially bottom: y=1050, h=60 -> clamped to y=1050, h=30
        r_bottom = Rect(100, 1050, 50, 60)
        sanitized_bottom = sanitize_rect(r_bottom, screen_size=screen)
        assert sanitized_bottom == Rect(100, 1050, 50, 30)

    def test_clamped_dimensions_too_small_rejected(self):
        from open_alo_core import Rect, sanitize_rect

        screen = (1920, 1080)
        # x=1919, w=10 -> overlaps by 1px -> should be rejected
        r = Rect(1919, 100, 10, 50)
        assert sanitize_rect(r, screen_size=screen) is None


class TestMapGlobalToStream:
    """map_global_to_stream() — transforms global to stream coordinates."""

    def test_with_stream_offset(self):
        from open_alo_core import Point, map_global_to_stream

        stream = {"position": (1432, 0), "size": (1854, 1048)}
        pt = Point(1500, 200)
        mapped = map_global_to_stream(pt, stream)
        assert mapped == Point(68, 200)

    def test_with_no_offset(self):
        from open_alo_core import Point, map_global_to_stream

        stream = {"position": (0, 0), "size": (1920, 1080)}
        pt = Point(500, 300)
        mapped = map_global_to_stream(pt, stream)
        assert mapped == Point(500, 300)

    def test_with_missing_position(self):
        from open_alo_core import Point, map_global_to_stream

        stream = {"size": (1920, 1080)}
        pt = Point(500, 300)
        mapped = map_global_to_stream(pt, stream)
        assert mapped == Point(500, 300)

    def test_with_empty_dict(self):
        from open_alo_core import Point, map_global_to_stream

        mapped = map_global_to_stream(Point(100, 200), {})
        assert mapped == Point(100, 200)


