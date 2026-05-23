"""
Unit tests for WindowManager data types and D-Bus response parsing.

Uses mocked subprocess to avoid requiring the Window Calls extension.
"""

import json
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

# Ensure src/ is on sys.path if package isn't installed
_src = str(Path(__file__).parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


class TestWindowInfo:
    """WindowInfo dataclass."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from open_alo_core import WindowInfo

        self.cls = WindowInfo

    def test_construction_with_defaults(self):
        win = self.cls(id=12345, wm_class="firefox", wm_class_instance="Firefox")
        assert win.id == 12345
        assert win.wm_class == "firefox"
        assert win.title == ""
        assert win.pid == 0
        assert win.focus is False

    def test_construction_full(self):
        win = self.cls(
            id=42,
            wm_class="Code",
            wm_class_instance="code-oss",
            title="test.py — Visual Studio Code",
            pid=1234,
            x=100,
            y=50,
            width=1200,
            height=800,
            workspace=1,
            monitor=0,
            focus=True,
            maximized=1,
        )
        assert win.title == "test.py — Visual Studio Code"
        assert win.focus is True
        assert win.width == 1200

    def test_repr(self):
        win = self.cls(id=1, wm_class="Terminal", wm_class_instance="gnome-terminal")
        assert "WindowInfo" in repr(win)
        assert "Terminal" in repr(win)

    def test_all_fields_present(self):
        """Ensure all expected fields exist on the dataclass."""
        win = self.cls(id=0, wm_class="", wm_class_instance="")
        fields = {f.name for f in win.__dataclass_fields__.values()}
        expected = {
            "id",
            "wm_class",
            "wm_class_instance",
            "title",
            "pid",
            "x",
            "y",
            "width",
            "height",
            "workspace",
            "monitor",
            "frame_type",
            "window_type",
            "focus",
            "in_current_workspace",
            "maximized",
        }
        assert fields == expected


class TestWindowType:
    """WindowType IntEnum."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from open_alo_core import WindowType

        self.cls = WindowType

    def test_values(self):
        assert self.cls.NORMAL == 0
        assert self.cls.DESKTOP == 1
        assert self.cls.DIALOG == 3
        assert self.cls.MODAL_DIALOG == 4

    def test_integer_cast(self):
        assert int(self.cls.NORMAL) == 0
        assert int(self.cls.DOCK) == 2


class TestFrameType:
    """FrameType IntEnum."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from open_alo_core import FrameType

        self.cls = FrameType

    def test_values(self):
        assert self.cls.NORMAL == 0
        assert self.cls.FRAMELESS == 1


class TestWindowManagerDBusResponseParsing:
    """WindowManager D-Bus JSON response parsing.
    
    All tests mock subprocess.run so they don't require a real GNOME session.
    """

    @pytest.fixture(autouse=True)
    def setup(self, mock_subprocess):
        from open_alo_core import WindowManager

        self.cls = WindowManager
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "(true, '[{\"id\":0,\"wm_class\":\"mock\",\"wm_class_instance\":\"Mock\",\"title\":\"Mock\"}]')"

    def test_parse_json_list_response(self):
        """Parse D-Bus response wrapping a JSON array."""
        wm = self.cls()

        response = "('[{\"id\":1,\"wm_class\":\"firefox\",\"wm_class_instance\":\"Firefox\",\"title\":\"Mozilla Firefox\"}]',)"

        result = wm._parse_json_response(response)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["wm_class"] == "firefox"

    def test_parse_json_single_response(self):
        """Parse D-Bus response wrapping a JSON object."""
        wm = self.cls()
        response = "('{\"x\":100,\"y\":200,\"width\":800,\"height\":600}',)"

        result = wm._parse_json_response(response)
        assert result is not None
        assert result["x"] == 100
        assert result["width"] == 800

    def test_parse_null_response(self):
        wm = self.cls()
        assert wm._parse_json_response(None) is None

    def test_parse_empty_response(self):
        wm = self.cls()
        assert wm._parse_json_response("") is None

    def test_parse_invalid_response(self):
        """Invalid JSON should return None."""
        wm = self.cls()
        result = wm._parse_json_response("not json")
        assert result is None, f"Expected None, got {result!r}"

    def test_list_windows_empty_on_failure(self):
        """list_windows returns empty list on D-Bus failure."""
        wm = self.cls()
        with patch.object(wm, "_dbus_call", return_value=None):
            windows = wm.list_windows()
            assert windows == []

    def test_list_windows_with_mock_data(self):
        """list_windows parses WindowInfo correctly."""
        wm = self.cls()
        mock_json = json.dumps([
            {
                "id": 100,
                "wm_class": "firefox",
                "wm_class_instance": "Firefox",
                "title": "Mozilla Firefox",
                "pid": 1234,
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080,
                "workspace": 0,
                "monitor": 0,
                "frame_type": 0,
                "window_type": 0,
                "focus": True,
                "in_current_workspace": True,
                "maximized": 1,
            },
            {
                "id": 101,
                "wm_class": "gnome-terminal",
                "wm_class_instance": "Gnome-terminal",
                "title": "Terminal",
                "pid": 5678,
                "x": 100,
                "y": 100,
                "width": 800,
                "height": 600,
                "workspace": 0,
                "monitor": 0,
                "frame_type": 0,
                "window_type": 0,
                "focus": False,
                "in_current_workspace": True,
                "maximized": 0,
            },
        ])
        dbus_response = f"('{mock_json}',)"

        with patch.object(wm, "_dbus_call", return_value=dbus_response):
            windows = wm.list_windows()
            assert len(windows) == 2
            assert windows[0].wm_class == "firefox"
            assert windows[0].focus is True
            assert windows[1].title == "Terminal"

    def test_find_window_by_wm_class(self):
        """find_window searches wm_class first."""
        from open_alo_core.window_manager import WindowInfo

        wm = self.cls()
        win1 = WindowInfo(id=1, wm_class="firefox", wm_class_instance="Firefox", title="Browser")
        win2 = WindowInfo(id=2, wm_class="Code", wm_class_instance="code-oss", title="test.py")

        with patch.object(wm, "list_windows", return_value=[win1, win2]):
            found = wm.find_window("Code")
            assert found is not None
            assert found.id == 2

            found = wm.find_window("firefox")
            assert found is not None
            assert found.id == 1

            found = wm.find_window("nonexistent")
            assert found is None

    def test_get_focused_window(self):
        """get_focused_window returns the focused window."""
        from open_alo_core.window_manager import WindowInfo

        wm = self.cls()
        win1 = WindowInfo(id=1, wm_class="a", wm_class_instance="A", focus=False)
        win2 = WindowInfo(id=2, wm_class="b", wm_class_instance="B", focus=True)

        with patch.object(wm, "list_windows", return_value=[win1, win2]):
            focused = wm.get_focused_window()
            assert focused is not None
            assert focused.id == 2

        with patch.object(wm, "list_windows", return_value=[win1]):
            assert wm.get_focused_window() is None

    def test_activate_returns_bool(self):
        wm = self.cls()
        with patch.object(wm, "_dbus_call", return_value="success"):
            assert wm.activate(123) is True
        with patch.object(wm, "_dbus_call", return_value=None):
            assert wm.activate(123) is False
