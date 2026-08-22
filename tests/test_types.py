"""
Unit tests for open_alo_core data types: Point, Size, Rect, normalize_key.
"""

import pytest

from open_alo_core import BUTTON_LEFT, BUTTON_MIDDLE, BUTTON_RIGHT, Point, Rect, Size
from open_alo_core.types import KEY_ALIASES, normalize_key


class TestPoint:
    """Point(NamedTuple) — 2D screen coordinates."""

    def test_construction(self):
        p = Point(100, 200)
        assert p.x == 100
        assert p.y == 200

    def test_repr(self):
        assert repr(Point(10, 20)) == "Point(10, 20)"

    def test_immutable(self):
        p = Point(1, 2)
        with pytest.raises(AttributeError):
            p.x = 99  # NamedTuple is immutable

    def test_unpacking(self):
        x, y = Point(30, 40)
        assert x == 30
        assert y == 40

    def test_equality(self):
        assert Point(5, 5) == Point(5, 5)
        assert Point(5, 5) != Point(5, 6)


class TestSize:
    """Size(NamedTuple) — width/height dimensions."""

    def test_construction(self):
        s = Size(1920, 1080)
        assert s.width == 1920
        assert s.height == 1080

    def test_repr(self):
        assert repr(Size(800, 600)) == "Size(800, 600)"

    def test_equality(self):
        assert Size(100, 200) == Size(100, 200)


class TestRect:
    """Rect(NamedTuple) — positioned rectangle."""

    def test_construction(self):
        r = Rect(10, 20, 800, 600)
        assert r.x == 10
        assert r.y == 20
        assert r.width == 800
        assert r.height == 600

    def test_repr(self):
        assert repr(Rect(0, 0, 100, 100)) == "Rect(0, 0, 100, 100)"

    @pytest.mark.parametrize(
        "rect,expected_center",
        [
            (Rect(0, 0, 100, 100), Point(50, 50)),
            (Rect(10, 20, 800, 600), Point(410, 320)),
            (Rect(100, 100, 1, 1), Point(100, 100)),
        ],
    )
    def test_center(self, rect, expected_center):
        assert rect.center == expected_center

    def test_top_left(self):
        assert Rect(10, 20, 800, 600).top_left == Point(10, 20)

    def test_bottom_right(self):
        assert Rect(10, 20, 800, 600).bottom_right == Point(810, 620)

    @pytest.mark.parametrize(
        "rect,point,expected",
        [
            (Rect(0, 0, 100, 100), Point(50, 50), True),
            (Rect(0, 0, 100, 100), Point(0, 0), True),
            (Rect(0, 0, 100, 100), Point(100, 100), True),
            (Rect(0, 0, 100, 100), Point(101, 50), False),
            (Rect(0, 0, 100, 100), Point(-1, 50), False),
            (Rect(10, 20, 100, 200), Point(60, 120), True),
        ],
    )
    def test_contains(self, rect, point, expected):
        assert rect.contains(point) == expected


class TestButtonConstants:
    """Mouse button constants."""

    def test_values(self):
        assert BUTTON_LEFT == 1
        assert BUTTON_MIDDLE == 2
        assert BUTTON_RIGHT == 3


class TestNormalizeKey:
    """Key name normalization."""

    @pytest.mark.parametrize(
        "input_key,expected",
        [
            ("enter", "Return"),
            ("return", "Return"),
            ("esc", "Escape"),
            ("escape", "Escape"),
            ("ctrl", "Control"),
            ("control", "Control"),
            ("alt", "Alt"),
            ("shift", "Shift"),
            ("super", "Super"),
            ("win", "Super"),
            ("cmd", "Super"),
            ("command", "Super"),
            ("tab", "Tab"),
            ("backspace", "BackSpace"),
            ("del", "Delete"),
            ("delete", "Delete"),
            ("home", "Home"),
            ("end", "End"),
            ("left", "Left"),
            ("right", "Right"),
            ("up", "Up"),
            ("down", "Down"),
            ("pageup", "Page_Up"),
            ("pagedown", "Page_Down"),
            ("Return", "Return"),  # Already normalized
            ("space", "space"),
        ],
    )
    def test_known_aliases(self, input_key, expected):
        assert normalize_key(input_key) == expected


    def test_unknown_key_passthrough(self):
        """Unknown keys should pass through unchanged."""
        assert normalize_key("F1") == "F1"
        assert normalize_key("a") == "a"
        assert normalize_key("Hyper_L") == "Hyper_L"

    def test_aliases_are_case_insensitive(self):
        assert normalize_key("CTRL") == "Control"
        assert normalize_key("Enter") == "Return"
        assert normalize_key("ESC") == "Escape"

    def test_alias_dict_coverage(self):
        """All KEY_ALIASES values should round-trip."""
        for alias, standard in KEY_ALIASES.items():
            assert normalize_key(alias) == standard


class TestStreamGeometry:
    """StreamGeometry dataclass."""

    def test_construction_and_properties(self):
        from open_alo_core import StreamGeometry
        sg = StreamGeometry(
            position=(100, 200),
            size=(1920, 1080),
            logical_size=(1920, 1080),
            scale=1.0,
            node_id=42,
            source_type=1,
        )
        assert sg.position == (100, 200)
        assert sg.size == (1920, 1080)
        assert sg.width == 1920
        assert sg.height == 1080
        assert sg.rect == Rect(100, 200, 1920, 1080)
        assert sg.node_id == 42
        assert sg.source_type == 1

    def test_is_in_stream(self):
        from open_alo_core import StreamGeometry
        sg = StreamGeometry(position=(0, 0), size=(1920, 1080))
        assert sg.is_in_stream(Rect(100, 100, 200, 200)) is True
        assert sg.is_in_stream(Rect(2000, 100, 100, 100)) is False
        assert sg.is_in_stream(Rect(0, 0, 1, 1)) is False  # Degenerate

    def test_clamp_to_stream(self):
        from open_alo_core import StreamGeometry
        sg = StreamGeometry(position=(0, 0), size=(1920, 1080))
        clamped = sg.clamp_to_stream(Rect(-50, -50, 200, 200))
        assert clamped == Rect(0, 0, 150, 150)
        assert sg.clamp_to_stream(Rect(2500, 2500, 100, 100)) is None

    def test_coordinate_mapping(self):
        from open_alo_core import StreamGeometry
        sg = StreamGeometry(position=(100, 50), size=(1920, 1080))
        pt_stream = Point(20, 30)
        pt_global = sg.stream_to_global_point(pt_stream)
        assert pt_global == Point(120, 80)
        assert sg.global_to_stream_point(pt_global) == pt_stream

    def test_dict_compatibility(self):
        from open_alo_core import StreamGeometry
        sg = StreamGeometry(position=(0, 0), size=(1920, 1080), scale=1.5)
        assert sg["size"] == (1920, 1080)
        assert sg["scale"] == 1.5
        assert sg.get("position") == (0, 0)
        assert sg.get("nonexistent", "fallback") == "fallback"
        d = sg.to_dict()
        assert d["size"] == (1920, 1080)
        assert d["scale"] == 1.5
