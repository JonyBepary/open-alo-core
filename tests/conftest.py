"""
Pytest configuration and shared fixtures for open_alo_core tests.

Provides PyGObject mocking so tests can run without a Wayland/GNOME session.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure src/ is on sys.path BEFORE any test imports the package,
# so the current source is used instead of any previously installed version.
_src_path = str(Path(__file__).parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# ---------------------------------------------------------------------------
# PyGObject mock setup (runs BEFORE any test file imports real gi modules)
# ---------------------------------------------------------------------------
# We patch sys.modules so that 'gi' and all gi.repository.* modules are
# MagicMock stubs instead of the real C-extension PyGObject bindings.
# This lets us import open_alo_core modules in CI/test without a display server.

_gi = MagicMock()
_gi_repo = MagicMock()
_gio = MagicMock()
_glib = MagicMock()
_gst = MagicMock()

# Configure commonly accessed attributes so code doesn't AttributeError
_gio.BusType.SESSION = 0
_gio.DBusProxyFlags.NONE = 0
_gio.DBusCallFlags.NONE = 0
_gio.DBusConnection = MagicMock
_gio.DBusProxy = MagicMock
_gio.DBusProxy.new_sync = MagicMock(return_value=MagicMock())

class _MockVariantMeta(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls._mock = MagicMock()

    def __call__(cls, *args, **kwargs):
        cls._mock(*args, **kwargs)
        inst = super().__call__(*args, **kwargs)
        return inst

    def __getattr__(cls, item):
        return getattr(cls._mock, item)


class MockVariant(metaclass=_MockVariantMeta):
    def __init__(self, sig=None, val=None):
        self.sig = sig
        self.val = val

    def get_string(self):
        return str(self.val) if self.val is not None else "mock_token"

    def get_boolean(self):
        return True

    def __repr__(self):
        return f"<Variant({self.sig!r}, {self.val!r})>"


_glib.MainLoop = MagicMock(return_value=MagicMock())
_glib.MainLoop.return_value.run = MagicMock()
_glib.MainLoop.return_value.quit = MagicMock()
_glib.timeout_add_seconds = MagicMock(return_value=42)
_glib.source_remove = MagicMock(return_value=True)
_glib.Variant = MockVariant



_gst.StateChangeReturn.SUCCESS = 0
_gst.StateChangeReturn.FAILURE = 1
_gst.StateChangeReturn.ASYNC = 2
_gst.State.NULL = 0
_gst.State.PLAYING = 2
_gst.State.PAUSED = 1
_gst.CLOCK_TIME_NONE = -1
_gst.MapFlags.READ = 1
_gst.Pipeline = MagicMock
_gst.Element = MagicMock
_gst.parse_launch = MagicMock(return_value=MagicMock())
_gst.init = MagicMock()
_gst.SECOND = 1000000000

_gst.FlowReturn.OK = 0
_gst.FlowReturn.ERROR = -1

# ---------------------------------------------------------------------------
# Apply mocks at MODULE level (not in a fixture) so they're active during
# pytest test-collection phase.  If test files import open_alo_core at
# module level (before fixtures run), the real gi C extensions would be
# loaded into sys.modules, causing segfaults during garbage collection
# when mock objects and real C objects coexist.
# ---------------------------------------------------------------------------
_pygobject_patch = patch.dict(
    sys.modules,
    {
        "gi": _gi,
        "gi.repository": _gi_repo,
        "gi.repository.Gio": _gio,
        "gi.repository.GLib": _glib,
        "gi.repository.Gst": _gst,
    },
    clear=False,
)
_pygobject_patch.start()


@pytest.fixture
def mock_dbus_portal():
    """Create a mock D-Bus portal proxy for testing portal interactions."""
    portal = MagicMock()
    # Simulate call_sync returning a request path
    portal.call_sync.return_value = ("/org/freedesktop/portal/desktop/request/1",)
    return portal


@pytest.fixture
def mock_bus():
    """Create a mock D-Bus connection that invokes signal callbacks immediately.

    Simulates a portal Response signal so portal_request() doesn't hang.
    The callback receives error_code=0 and an empty results dict.
    """
    bus = MagicMock()

    def _signal_subscribe(bus_name, iface, signal, path, arg0, flags, callback):
        """Invoke callback immediately to simulate portal response."""
        callback(
            None,  # connection
            bus_name,  # sender name
            path,  # object path
            iface,  # interface name
            signal,  # signal name
            (0, {}),  # (error_code, results) — success
        )
        return 1  # subscription id

    bus.signal_subscribe.side_effect = _signal_subscribe
    return bus


@pytest.fixture
def ensure_package_path():
    """Ensure src/ is on sys.path for test imports."""
    from pathlib import Path

    src = str(Path(__file__).parent.parent / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    yield


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run to prevent real D-Bus calls in WindowManager tests."""
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock()
        mock.return_value.returncode = 0
        mock.return_value.stdout = "(true, '[]')"
        yield mock
