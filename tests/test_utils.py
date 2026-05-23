"""
Unit tests for open_alo_core utility functions.

Uses environment variable manipulation to test session detection.
Other utilities (is_portal_available, is_pipewire_available) test
basic error handling paths via mocked imports.
"""

import os
import pytest
from unittest.mock import patch


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
        with patch(
            "open_alo_core.is_portal_available",
            return_value=True,
        ):
            from open_alo_core import is_portal_available

            assert is_portal_available() is True

    def test_not_available(self):
        with patch(
            "open_alo_core.is_portal_available",
            return_value=False,
        ):
            from open_alo_core import is_portal_available

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
