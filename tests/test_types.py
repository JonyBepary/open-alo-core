"""
Unit tests for open_alo_core data types: Point, Size, Rect, normalize_key.
"""

import pytest
from open_alo_core import Point, Size, Rect, BUTTON_LEFT, BUTTON_MIDDLE, BUTTON_RIGHT
from open_alo_core.types import normalize_key, KEY_ALIASES


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
