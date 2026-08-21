"""
Unit tests for WindowManager data types, D-Bus response parsing, and window actions.

Uses mocked subprocess to avoid requiring the Window Calls extension.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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
    """WindowManager D-Bus JSON response parsing."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_subprocess):
        from open_alo_core import WindowManager

        self.cls = WindowManager
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = '(true, \'[{"id":0,"wm_class":"mock","wm_class_instance":"Mock","title":"Mock"}]\')'

    def test_parse_json_list_response(self):
        """Parse D-Bus response wrapping a JSON array."""
        wm = self.cls()
        response = '(\'[{"id":1,"wm_class":"firefox","wm_class_instance":"Firefox","title":"Mozilla Firefox"}]\',)'

        result = wm._parse_json_response(response)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["wm_class"] == "firefox"

    def test_parse_json_single_response(self):
        """Parse D-Bus response wrapping a JSON object."""
        wm = self.cls()
        response = '(\'{"x":100,"y":200,"width":800,"height":600}\',)'

        result = wm._parse_json_response(response)
        assert result is not None
        assert result["x"] == 100
        assert result["width"] == 800

    def test_parse_json_unicode_escaped(self):
        """Parse D-Bus response containing unicode escaped sequences."""
        wm = self.cls()
        response = r"('{\"title\": \"Hello \u0026 World\"}',)"
        result = wm._parse_json_response(response)
        assert result == {"title": "Hello & World"}

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
        mock_json = json.dumps(
            [
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
                    "workspace": 1,
                    "monitor": 0,
                    "frame_type": 0,
                    "window_type": 0,
                    "focus": False,
                    "in_current_workspace": False,
                    "maximized": 0,
                },
            ]
        )
        dbus_response = f"('{mock_json}',)"

        with patch.object(wm, "_dbus_call", return_value=dbus_response):
            windows = wm.list_windows()
            assert len(windows) == 2
            assert windows[0].wm_class == "firefox"
            assert windows[0].focus is True
            assert windows[1].title == "Terminal"

            # Filter current_workspace_only
            current_only = wm.list_windows(current_workspace_only=True)
            assert len(current_only) == 1
            assert current_only[0].id == 100

    def test_find_window_by_wm_class_and_title(self):
        """find_window searches wm_class first, then title."""
        from open_alo_core.window_manager import WindowInfo

        wm = self.cls()
        win1 = WindowInfo(
            id=1, wm_class="firefox", wm_class_instance="Firefox", title="Google Search"
        )
        win2 = WindowInfo(
            id=2, wm_class="Code", wm_class_instance="code-oss", title="test.py"
        )

        with patch.object(wm, "list_windows", return_value=[win1, win2]):
            # wm_class match
            assert wm.find_window("Code").id == 2
            # title fallback match
            assert wm.find_window("Google").id == 1
            # title match disabled
            assert wm.find_window("Google", match_title=False) is None
            # nonexistent
            assert wm.find_window("nonexistent") is None

    def test_find_all_windows(self):
        from open_alo_core.window_manager import WindowInfo

        wm = self.cls()
        win1 = WindowInfo(id=1, wm_class="firefox", wm_class_instance="Firefox", title="Tab 1")
        win2 = WindowInfo(id=2, wm_class="firefox", wm_class_instance="Firefox", title="Tab 2")
        win3 = WindowInfo(id=3, wm_class="code", wm_class_instance="code", title="Editor")

        with patch.object(wm, "list_windows", return_value=[win1, win2, win3]):
            found = wm.find_all_windows("firefox")
            assert len(found) == 2
            assert [w.id for w in found] == [1, 2]

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


class TestWindowManagerActions:
    """Test all WindowManager state and manipulation actions."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_subprocess):
        from open_alo_core import WindowManager

        self.cls = WindowManager
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = '(true, \'[]\')'

    def test_window_state_methods(self):
        wm = self.cls()
        methods = [
            ("activate", "Activate", (100,)),
            ("maximize", "Maximize", (100,)),
            ("unmaximize", "Unmaximize", (100,)),
            ("minimize", "Minimize", (100,)),
            ("unminimize", "Unminimize", (100,)),
            ("close", "Close", (100,)),
            ("make_fullscreen", "MakeFullscreen", (100,)),
            ("unmake_fullscreen", "UnmakeFullscreen", (100,)),
            ("move", "Move", (100, 10, 20)),
            ("resize", "Resize", (100, 800, 600)),
            ("move_resize", "MoveResize", (100, 10, 20, 800, 600)),
            ("move_to_workspace", "MoveToWorkspace", (100, 2)),
        ]

        for py_method, dbus_method, args in methods:
            with patch.object(wm, "_dbus_call", return_value="success") as mock_dbus:
                fn = getattr(wm, py_method)
                assert fn(*args) is True
                mock_dbus.assert_called_once_with(dbus_method, *args)

            with patch.object(wm, "_dbus_call", return_value=None):
                fn = getattr(wm, py_method)
                assert fn(*args) is False

    def test_toggle_fullscreen(self):
        wm = self.cls()
        # When window is currently fullscreen -> should call unmake_fullscreen
        with (
            patch.object(wm, "get_details", return_value={"fullscreen": True}),
            patch.object(wm, "unmake_fullscreen", return_value=True) as mock_unmake,
            patch.object(wm, "make_fullscreen") as mock_make,
        ):
            assert wm.toggle_fullscreen(100) is True
            mock_unmake.assert_called_once_with(100)
            mock_make.assert_not_called()

        # When window is not fullscreen -> should call make_fullscreen
        with (
            patch.object(wm, "get_details", return_value={"fullscreen": False}),
            patch.object(wm, "unmake_fullscreen") as mock_unmake,
            patch.object(wm, "make_fullscreen", return_value=True) as mock_make,
        ):
            assert wm.toggle_fullscreen(100) is True
            mock_make.assert_called_once_with(100)
            mock_unmake.assert_not_called()

    def test_get_details(self):
        wm = self.cls()
        with patch.object(wm, "_dbus_call", return_value="('{\"id\": 100}',)"):
            details = wm.get_details(100)
            assert details == {"id": 100}

        with patch.object(wm, "_dbus_call", return_value=None):
            assert wm.get_details(100) is None

    def test_get_title(self):
        wm = self.cls()
        with patch.object(wm, "_dbus_call", return_value="('My Window Title',)") as mock_call:
            title = wm.get_title(100)
            assert title == "My Window Title"

        with patch.object(wm, "_dbus_call", return_value=None):
            assert wm.get_title(100) is None

    def test_get_frame_rect_and_bounds(self):
        wm = self.cls()
        with patch.object(wm, "_dbus_call", return_value="('{\"x\": 10, \"y\": 20}',)"):
            assert wm.get_frame_rect(100) == {"x": 10, "y": 20}
            assert wm.get_frame_bounds(100) == {"x": 10, "y": 20}

        with patch.object(wm, "_dbus_call", return_value=None):
            assert wm.get_frame_rect(100) is None
            assert wm.get_frame_bounds(100) is None


class TestWindowManagerConvenienceFunctions:
    """Test module-level convenience functions."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = '(true, \'[]\')'

    def test_convenience_functions(self):
        import open_alo_core
        from open_alo_core.window_manager import WindowInfo

        mock_win = WindowInfo(id=42, wm_class="editor", wm_class_instance="Editor", title="Code")

        with patch.object(open_alo_core.WindowManager, "list_windows", return_value=[mock_win]):
            assert open_alo_core.list_windows() == [mock_win]

        with patch.object(open_alo_core.WindowManager, "find_window", return_value=mock_win):
            assert open_alo_core.find_window("editor") == mock_win

        with patch.object(open_alo_core.WindowManager, "get_focused_window", return_value=mock_win):
            assert open_alo_core.get_focused_window() == mock_win

        with patch.object(open_alo_core.WindowManager, "activate", return_value=True) as mock_act:
            assert open_alo_core.activate_window(42) is True
            mock_act.assert_called_with(42)

        with (
            patch.object(open_alo_core.WindowManager, "find_window", return_value=mock_win),
            patch.object(open_alo_core.WindowManager, "activate", return_value=True) as mock_act,
        ):
            assert open_alo_core.activate_window("editor") is True
            mock_act.assert_called_with(42)

        with patch.object(open_alo_core.WindowManager, "find_window", return_value=None):
            assert open_alo_core.activate_window("nonexistent") is False


class TestWindowManagerErrorHandling:
    """Test error handling and edge cases in WindowManager."""

    def test_check_extension_raises_runtime_error_on_exception(self):
        from open_alo_core import WindowManager

        with patch.object(WindowManager, "_dbus_call", side_effect=Exception("D-Bus failure")):
            with pytest.raises(RuntimeError, match="Window Calls extension not available"):
                WindowManager()

    def test_check_extension_raises_runtime_error_when_dbus_call_returns_none(self):
        from open_alo_core import WindowManager

        with patch.object(WindowManager, "_dbus_call", return_value=None):
            with pytest.raises(RuntimeError, match="Window Calls extension not available"):
                WindowManager()



    def test_dbus_call_non_zero_returncode(self):
        from open_alo_core import WindowManager

        mock_res = MagicMock()
        mock_res.returncode = 1
        with patch("subprocess.run", return_value=mock_res):
            wm = WindowManager.__new__(WindowManager)
            wm.timeout = 5
            assert wm._dbus_call("List") is None

    def test_list_windows_returns_empty_when_parse_fails(self):
        from open_alo_core import WindowManager

        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value.returncode = 0
            mock_sub.return_value.stdout = "('invalid json',)"
            wm = WindowManager()
            with patch.object(wm, "_parse_json_response", return_value=None):
                assert wm.list_windows() == []

