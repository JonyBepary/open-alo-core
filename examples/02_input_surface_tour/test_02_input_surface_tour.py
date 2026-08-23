"""
Headless tests for 02_input_surface_tour — no portal, no Wayland.

Validates preflight safety gates and guided tour run with mocks.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Bootstrap same as example.py — parents[2]/"src" + local dir for `import example`
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from open_alo_core.types import Point, Rect  # noqa: E402

# --- sibling example.py loader (unique module name; folders are not packages) ---
import pathlib
import importlib.util as _ilu

def _load_example_module():
    _here = pathlib.Path(__file__).resolve().parent
    _modname = "_showcase_" + "02_input_surface_tour"
    _spec = _ilu.spec_from_file_location(_modname, _here / "example.py")
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod

_ex = _load_example_module()

key_combo_normalization_demo = _ex.key_combo_normalization_demo
plan_injections = _ex.plan_injections
run = _ex.run

ex = _ex  # loaded sibling module instance (patch THIS in tests)



# ---------------------------------------------------------------------------
# Docs shape
# ---------------------------------------------------------------------------

def test_key_combo_docs_shape():
    docs = key_combo_normalization_demo()
    assert isinstance(docs, list)
    assert len(docs) >= 3
    # Each entry is (combo_input, description)
    for combo, desc in docs:
        assert isinstance(combo, list)
        assert isinstance(desc, str)
        assert len(desc) > 0
    # Must contain equivalence pair ["ctrl","a"] vs ["ctrl","A"]
    combos_str = [",".join(c).lower() for c, _ in docs]
    # at least one entry mentions ctrl+a and one mentions ctrl+A (case-insensitive)
    # We check raw combos
    flat = [tuple(c) for c, _ in docs]
    assert ("ctrl", "a") in flat
    assert ("ctrl", "A") in flat
    # Must contain ["ctrl","shift","s"] (case-insensitive for s)
    assert any(c == ("ctrl", "shift", "s") or c == ("ctrl", "shift", "S") for c in flat)
    # One description must mention equivalence / lowercased
    all_desc = " ".join(d for _, d in docs).lower()
    assert "lowercase" in all_desc or "equivalent" in all_desc or "shift" in all_desc


# ---------------------------------------------------------------------------
# plan_injections — safe center
# ---------------------------------------------------------------------------

def test_plan_injections_safe_center():
    # Big window covering full screen, bottom->top z_order [1]
    rects = {1: Rect(0, 0, 1920, 1080)}
    z_order = [1]
    center = Point(960, 540)
    result = plan_injections([center], rects, z_order, target_win_id=1, stream_size=(1920, 1080))
    assert len(result) == 1
    pt, is_safe, reason = result[0]
    assert pt == center
    assert is_safe is True
    assert isinstance(reason, str)
    assert len(reason) > 0


# ---------------------------------------------------------------------------
# plan_injections — occluded
# ---------------------------------------------------------------------------

def test_plan_injections_occluded():
    # Two windows: lower 1 covers full screen, higher 2 covers center 200x200 at (800,400)
    rects = {
        1: Rect(0, 0, 1920, 1080),
        2: Rect(800, 400, 400, 400),
    }
    z_order = [1, 2]  # 2 is on top
    pt = Point(900, 500)  # inside higher window rect
    result = plan_injections([pt], rects, z_order, target_win_id=1, stream_size=(1920, 1080))
    assert len(result) == 1
    _, is_safe, reason = result[0]
    assert is_safe is False
    assert "occluded" in reason.lower()


# ---------------------------------------------------------------------------
# plan_injections — bounds edge
# ---------------------------------------------------------------------------

def test_plan_injections_bounds_edge():
    rects = {1: Rect(0, 0, 1920, 1080)}
    z_order = [1]
    pt = Point(5000, 500)
    result = plan_injections([pt], rects, z_order, target_win_id=1, stream_size=(1920, 1080))
    assert len(result) == 1
    _, is_safe, reason = result[0]
    assert is_safe is False
    # Bounds failure mentions sentinel/bounds or screen size
    assert "bounds" in reason.lower() or "sentinel" in reason.lower() or "screen" in reason.lower()


# ---------------------------------------------------------------------------
# run with mocks — headless
# ---------------------------------------------------------------------------

def test_run_with_mocks():
    desktop = MagicMock()
    # Make config properties behave like real values (not MagicMock) for readability
    desktop.pause = 0.05
    desktop.fail_safe = False
    desktop.touch_mode = False
    # Ensure methods are MagicMocks that record calls
    # click returns timestamp int
    desktop.click.return_value = 123456789
    desktop.double_click.return_value = None
    desktop.move_mouse.return_value = None
    desktop.type_text.return_value = None
    desktop.press_key.return_value = 123456789
    desktop.key_combo.return_value = None
    desktop.scroll.return_value = None
    desktop.hscroll.return_value = None
    desktop.smooth_scroll.return_value = None
    desktop.drag.return_value = None
    desktop.swipe.return_value = None
    desktop.move_mouse_relative.return_value = None
    desktop.press_keys.return_value = None
    # hold_key must be a contextmanager
    from contextlib import contextmanager

    @contextmanager
    def _fake_hold(key):
        yield

    desktop.hold_key = _fake_hold
    # get_screen_size optional
    desktop.get_screen_size.return_value = (1920, 1080)
    desktop.get_stream_info.return_value = None

    wm = MagicMock()
    wm.get_window_z_order.return_value = [1]
    wm.list_windows.return_value = []
    wm.get_focused_window.return_value = None

    demonstrated = run(desktop=desktop, wm=wm)

    assert isinstance(demonstrated, int)
    assert 0 <= demonstrated <= 12

    # Must have exercised input injectors
    assert desktop.click.call_count >= 2, f"click called {desktop.click.call_count} times, expected >=2"
    assert desktop.smooth_scroll.call_count >= 1, f"smooth_scroll called {desktop.smooth_scroll.call_count} times, expected >=1"
