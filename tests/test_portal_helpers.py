"""
Unit tests for the shared portal helper modules.

Tests char_to_keysym mapping correctness and the portal_request helper.
PyGObject is mocked via conftest.py.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure src/ is on sys.path for importing internal modules
_src = str(Path(__file__).parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


class TestCharToKeysym:
    """char_to_keysym() — character/name to X11 keysym mapping."""

    @pytest.fixture(autouse=True)
    def import_module(self):
        from open_alo_core.wayland._portal_helpers import char_to_keysym

        self.char_to_keysym = char_to_keysym

    @pytest.mark.parametrize(
        "key_name,expected_keysym",
        [
            ("Return", 0xFF0D),
            ("Escape", 0xFF1B),
            ("Tab", 0xFF09),
            ("BackSpace", 0xFF08),
            ("Delete", 0xFFFF),
            ("Left", 0xFF51),
            ("Up", 0xFF52),
            ("Right", 0xFF53),
            ("Down", 0xFF54),
            ("Control", 0xFFE3),
            ("Alt", 0xFFE9),
            ("Shift", 0xFFE1),
            ("Super", 0xFFEB),
            (" ", 0x0020),
        ],
    )
    def test_special_keys(self, key_name, expected_keysym):
        assert self.char_to_keysym(key_name) == expected_keysym

    @pytest.mark.parametrize(
        "char,expected",
        [
            ("a", ord("a")),
            ("A", ord("A")),
            ("1", ord("1")),
            (".", ord(".")),
            ("~", ord("~")),
            ("\n", 10),  # newline = unicode/ASCII line feed
        ],
    )
    def test_single_characters(self, char, expected):
        assert self.char_to_keysym(char) == expected

    def test_empty_string(self):
        assert self.char_to_keysym("") == 0

    def test_multiple_characters(self):
        """Multi-char strings that aren't in the map should return 0."""
        assert self.char_to_keysym("abc") == 0
        assert self.char_to_keysym("Ctrl") == 0  # case-sensitive, expects "Control"

    def test_case_sensitive(self):
        """The mapping is case-sensitive for special names."""
        assert self.char_to_keysym("return") == 0  # lowercase not in map
        assert self.char_to_keysym("RETURN") == 0  # uppercase not in map

    def test_unicode_values_is_valid_keysym(self):
        """All single Unicode chars should produce valid keysym values (0x0000-0x10FFFF)."""
        for c in "hello 123 !@#$%^&*()_+-=[]{}|;':\",./<>?`~":
            keysym = self.char_to_keysym(c)
            assert 0 <= keysym <= 0x10FFFF

    @pytest.mark.parametrize(
        "char,expected_keysym",
        [
            ("আ", 0x01000000 | ord("আ")),
            ("ল", 0x01000000 | ord("ল")),
            ("া", 0x01000000 | ord("া")),
            ("€", 0x01000000 | ord("€")),
            ("語", 0x01000000 | ord("語")),
            ("🚀", 0x01000000 | ord("🚀")),
        ],
    )
    def test_non_latin_unicode_keysyms(self, char, expected_keysym):
        """Characters > 0xFF map to 0x01000000 | codepoint."""
        assert self.char_to_keysym(char) == expected_keysym



class TestPortalRequest:
    """portal_request() — async D-Bus request helper."""

    @pytest.fixture(autouse=True)
    def import_module(self):
        from gi.repository import GLib
        from open_alo_core.wayland._portal_helpers import portal_request

        self.portal_request = portal_request
        self.GLib = GLib

    def test_successful_response(self, mock_bus, mock_dbus_portal):
        """Happy path: portal returns error_code=0 and results."""
        expected_results = {"session_handle": "/session/123"}

        def _signal_subscribe(bus_name, iface, signal, path, arg0, flags, callback):
            callback(None, bus_name, path, iface, signal, (0, expected_results))
            return 1

        mock_bus.signal_subscribe.side_effect = _signal_subscribe
        error_code, results = self.portal_request(
            mock_bus, mock_dbus_portal, "CreateSession", MagicMock()
        )
        assert error_code == 0
        assert results == expected_results

    def test_uses_signal_subscribe(self, mock_bus, mock_dbus_portal):
        """Should subscribe to Response signal."""
        self.portal_request(mock_bus, mock_dbus_portal, "CreateSession", MagicMock())
        assert mock_bus.signal_subscribe.called

    def test_uses_timeout(self, mock_bus, mock_dbus_portal):
        """Should register a GLib timeout."""
        self.GLib.timeout_add_seconds.reset_mock()
        self.portal_request(mock_bus, mock_dbus_portal, "CreateSession", MagicMock())
        self.GLib.timeout_add_seconds.assert_called_once()
        args = self.GLib.timeout_add_seconds.call_args[0]
        assert args[0] == 30

    def test_custom_timeout(self, mock_bus, mock_dbus_portal):
        """Custom timeout_seconds should be respected."""
        self.GLib.timeout_add_seconds.reset_mock()
        self.portal_request(
            mock_bus,
            mock_dbus_portal,
            "CreateSession",
            MagicMock(),
            timeout_seconds=15,
        )
        args = self.GLib.timeout_add_seconds.call_args[0]
        assert args[0] == 15

    def test_cleans_up_timeout_and_signal(self, mock_bus, mock_dbus_portal):
        """Should remove timeout source and unsubscribe signal on completion."""
        self.GLib.source_remove.reset_mock()
        mock_bus.signal_unsubscribe.reset_mock()
        self.portal_request(mock_bus, mock_dbus_portal, "CreateSession", MagicMock())
        self.GLib.source_remove.assert_called_once()
        mock_bus.signal_unsubscribe.assert_called_once_with(1)


    def test_error_code_response(self, mock_bus, mock_dbus_portal):
        """Non-zero error code (e.g. 1 for user cancelled/denied)."""
        def _signal_subscribe(bus_name, iface, signal, path, arg0, flags, callback):
            callback(None, bus_name, path, iface, signal, (1, {}))
            return 1

        mock_bus.signal_subscribe.side_effect = _signal_subscribe
        error_code, results = self.portal_request(
            mock_bus, mock_dbus_portal, "CreateSession", MagicMock()
        )
        assert error_code == 1
        assert results == {}

    def test_timeout_expiry(self, mock_dbus_portal):
        """If response signal never arrives, timeout occurs and returns None."""
        bus = MagicMock()
        bus.signal_subscribe.return_value = 1  # Does not invoke callback

        error_code, results = self.portal_request(
            bus, mock_dbus_portal, "CreateSession", MagicMock(), timeout_seconds=5
        )
        assert error_code is None
        assert results is None

    def test_early_response_before_call_sync_returns(self, mock_bus, mock_dbus_portal):
        """When Response signal arrives synchronously upon subscription."""
        expected_results = {"session_handle": "/session/early_123"}

        def _signal_subscribe(bus_name, iface, signal, path, arg0, flags, callback):
            # Invoke callback synchronously during subscription
            callback(None, bus_name, "/org/freedesktop/portal/desktop/request/1/token", iface, signal, (0, expected_results))
            return 99

        mock_bus.signal_subscribe.side_effect = _signal_subscribe
        mock_dbus_portal.call_sync.return_value = ("/org/freedesktop/portal/desktop/request/1/token",)

        error_code, results = self.portal_request(
            mock_bus, mock_dbus_portal, "CreateSession", MagicMock()
        )
        assert error_code == 0
        assert results == expected_results


