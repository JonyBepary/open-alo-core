"""
Headless tests for 03_window_orchestra — no GNOME, no D-Bus.

Uses a FakeWM injected into example.run(wm=...).
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# Bootstrap same as example.py — parents[2]/"src"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# --- sibling example.py loader (unique module name; folders are not packages) ---
import pathlib
import importlib.util as _ilu

def _load_example_module():
    _here = pathlib.Path(__file__).resolve().parent
    _modname = "_showcase_" + "03_window_orchestra"
    _spec = _ilu.spec_from_file_location(_modname, _here / "example.py")
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod

_ex = _load_example_module()

classify_windows = _ex.classify_windows
utility_diff = _ex.utility_diff
run = _ex.run

ex = _ex  # loaded sibling module instance (patch THIS in tests)

from open_alo_core.window_manager import is_utility_window  # noqa: E402


# ---------------------------------------------------------------------------
# Minimal WindowInfo-like dataclass for fake (compatible with is_utility_window)
# ---------------------------------------------------------------------------

@dataclass
class FakeWindowInfo:
    id: int
    wm_class: str
    title: str = ""
    wm_class_instance: str = ""
    x: int = 0
    y: int = 0
    width: int = 800
    height: int = 600
    workspace: int = 0
    focus: bool = False
    maximized: int = 0


class FakeWM:
    """In-memory WindowManager double with call tracking."""

    def __init__(self, include_utility: bool = False):
        self.include_utility = include_utility
        self.timeout = 5
        self._is_utility_window = staticmethod(is_utility_window)  # type: ignore[attr-defined]
        # Pre-populate: one utility (gjs Desktop Icons), one normal, one editor
        self.windows: List[FakeWindowInfo] = [
            FakeWindowInfo(id=1, wm_class="gjs", title="Desktop Icons - test", focus=False),
            FakeWindowInfo(id=2, wm_class="org.gnome.TextEditor", title="Text Editor", focus=True, workspace=0),
            FakeWindowInfo(id=3, wm_class="firefox", title="Mozilla Firefox", focus=False),
        ]
        # Call trackers
        self.activate_calls: List[int] = []
        self.maximize_calls: List[int] = []
        self.unmaximize_calls: List[int] = []
        self.minimize_calls: List[int] = []
        self.unminimize_calls: List[int] = []
        self.close_calls: List[int] = []
        self.make_fullscreen_calls: List[int] = []
        self.unmake_fullscreen_calls: List[int] = []
        self.toggle_fullscreen_calls: List[int] = []
        self.move_resize_calls: List[tuple] = []
        self.move_to_workspace_calls: List[tuple] = []
        self._frame_rect: Dict[int, Dict] = {w.id: {"x": w.x, "y": w.y, "width": w.width, "height": w.height} for w in self.windows}

    # -- listing / search — mirrors window_manager.py:261, :244 etc --

    def list_windows(self, current_workspace_only: bool = False) -> List[FakeWindowInfo]:
        ws = self.windows
        if not self.include_utility:
            ws = [w for w in ws if not is_utility_window(w)]  # type: ignore[arg-type]
        if current_workspace_only:
            # simplified: return all when flag false? Fake has no workspace filtering beyond id
            pass
        return list(ws)

    def find_window(self, query: str, match_title: bool = True) -> Optional[FakeWindowInfo]:
        query_lower = query.lower()
        ws = self.list_windows()
        for w in ws:
            wc = (w.wm_class or "").lower()
            wi = (w.wm_class_instance or "").lower()
            if (query_lower in wc or (wc and wc in query_lower)) or (query_lower in wi or (wi and wi in query_lower)):
                return w
        if match_title:
            for w in ws:
                if query_lower in (w.title or "").lower():
                    return w
        return None

    def find_all_windows(self, query: str, match_title: bool = True) -> List[FakeWindowInfo]:
        q = query.lower()
        res = []
        for w in self.list_windows():
            if q in (w.wm_class or "").lower() or (match_title and q in (w.title or "").lower()):
                res.append(w)
        return res

    def get_focused_window(self) -> Optional[FakeWindowInfo]:
        for w in self.list_windows():
            if w.focus:
                return w
        return None

    def get_details(self, window_id: int) -> Optional[Dict]:
        w = next((x for x in self.windows if x.id == window_id), None)
        if not w:
            return None
        return {"id": w.id, "maximized": w.maximized, "canclose": True, "fullscreen": False, "title": w.title}

    def get_title(self, window_id: int) -> Optional[str]:
        w = next((x for x in self.windows if x.id == window_id), None)
        return w.title if w else None

    def get_window_z_order(self) -> List[int]:
        # Return ids in order bottom-to-top; scrub utility if include_utility False
        ids = [w.id for w in self.windows]
        if not self.include_utility:
            util_ids = {w.id for w in self.windows if is_utility_window(w)}  # type: ignore[arg-type]
            ids = [i for i in ids if i not in util_ids]
        return ids

    def wait_for_window(self, query: str, match_title: bool = True, timeout: float = 5, poll_interval: float = 0.05) -> Optional[FakeWindowInfo]:
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            win = self.find_window(query, match_title=match_title)
            if win:
                return win
            time.sleep(poll_interval)
        return None

    # -- mutations --

    def activate(self, window_id: int) -> bool:
        self.activate_calls.append(window_id)
        # Simulate z-order move to front
        w = next((x for x in self.windows if x.id == window_id), None)
        if w:
            self.windows.remove(w)
            self.windows.append(w)
        return True

    def maximize(self, window_id: int) -> bool:
        self.maximize_calls.append(window_id)
        w = next((x for x in self.windows if x.id == window_id), None)
        if w:
            w.maximized = 1
        return True

    def unmaximize(self, window_id: int) -> bool:
        self.unmaximize_calls.append(window_id)
        w = next((x for x in self.windows if x.id == window_id), None)
        if w:
            w.maximized = 0
        return True

    def minimize(self, window_id: int) -> bool:
        self.minimize_calls.append(window_id)
        return True

    def unminimize(self, window_id: int) -> bool:
        self.unminimize_calls.append(window_id)
        return True

    def close(self, window_id: int) -> bool:
        self.close_calls.append(window_id)
        self.windows = [w for w in self.windows if w.id != window_id]
        return True

    def make_fullscreen(self, window_id: int) -> bool:
        self.make_fullscreen_calls.append(window_id)
        return True

    def unmake_fullscreen(self, window_id: int) -> bool:
        self.unmake_fullscreen_calls.append(window_id)
        return True

    def toggle_fullscreen(self, window_id: int) -> bool:
        self.toggle_fullscreen_calls.append(window_id)
        # Real impl checks details then delegates; fake just records
        return True

    def move(self, window_id: int, x: int, y: int) -> bool:
        if window_id in self._frame_rect:
            self._frame_rect[window_id]["x"] = x
            self._frame_rect[window_id]["y"] = y
        return True

    def resize(self, window_id: int, width: int, height: int) -> bool:
        if window_id in self._frame_rect:
            self._frame_rect[window_id]["width"] = width
            self._frame_rect[window_id]["height"] = height
        return True

    def move_resize(self, window_id: int, x: int, y: int, width: int, height: int) -> bool:
        self.move_resize_calls.append((window_id, x, y, width, height))
        self._frame_rect[window_id] = {"x": x, "y": y, "width": width, "height": height}
        return True

    def get_frame_rect(self, window_id: int) -> Optional[Dict]:
        return dict(self._frame_rect.get(window_id, {"x": 0, "y": 0, "width": 800, "height": 600}))

    def get_frame_bounds(self, window_id: int) -> Optional[Dict]:
        return self.get_frame_rect(window_id)

    def move_to_workspace(self, window_id: int, ws: int) -> bool:
        self.move_to_workspace_calls.append((window_id, ws))
        w = next((x for x in self.windows if x.id == window_id), None)
        if w:
            w.workspace = ws
        return True


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_classify_flags_utility():
    util = FakeWindowInfo(id=10, wm_class="gjs", title="Desktop Icons something")
    normal = FakeWindowInfo(id=11, wm_class="firefox", title="Mozilla Firefox")
    null_class = FakeWindowInfo(id=12, wm_class="", title="dummy")
    result = classify_windows([util, normal, null_class])
    d = {w.id: flag for w, flag in result}
    assert d[10] is True, "gjs Desktop Icons should be utility"
    assert d[11] is False, "normal firefox should not be utility"
    assert d[12] is True, "null wm_class should be utility"

    # Also verify top-level is_utility_window matches
    assert is_utility_window(util) is True  # type: ignore[arg-type]
    assert is_utility_window(normal) is False  # type: ignore[arg-type]


def test_utility_diff_splits():
    wm = FakeWM(include_utility=True)
    all_windows = wm.list_windows()
    assert len(all_windows) == 3  # includes gjs utility
    kept, hidden = utility_diff(all_windows)
    assert len(hidden) == 1, f"expected 1 hidden utility, got {len(hidden)}"
    assert len(kept) == 2
    # Hidden should be the gjs one
    assert hidden[0].wm_class == "gjs"
    assert all(not is_utility_window(w) for w in kept)  # type: ignore[arg-type]


def test_run_restores_state_and_closes(monkeypatch, capsys):
    """
    run(fake_wm) with spawn patched to None (step 3 SKIPs) but remaining
    steps still execute against the pre-existing editor window.
    """
    wm = FakeWM(include_utility=False)
    # Capture original workspace of editor before run
    editor_before = wm.find_window("TextEditor")
    assert editor_before is not None
    orig_ws = editor_before.workspace

    # Patch spawn_editor to return None (FileNotFoundError guard path)
    # patch file-level `ex` (the importlib-loaded example module)

    monkeypatch.setattr(ex, "spawn_editor", lambda: None)
    # Speed up sleeps
    monkeypatch.setattr(time, "sleep", lambda *_: None)

    demonstrated = run(wm)

    out = capsys.readouterr().out
    # Footer present
    assert "Capabilities demonstrated" in out
    assert f"{demonstrated}/9" in out or f"{demonstrated} / 9" in out

    # Editor-path was skipped (spawn returned None)
    # run should have printed a SKIP for spawn but still found editor via wait_for_window
    # so activate/maximize etc were exercised
    assert len(wm.activate_calls) >= 1, "activate should have been called for editor"
    assert len(wm.maximize_calls) >= 1, "maximize should have been called"
    assert len(wm.unmaximize_calls) >= 1, "unmaximize (restore) should have been called"
    assert len(wm.toggle_fullscreen_calls) >= 1, "toggle_fullscreen should have been called"

    # Since we did NOT spawn a new window, close should NOT be called (preserve state)
    # Spec phrase: "close called for any opened id == none"
    assert len(wm.close_calls) == 0, f"should not close pre-existing window, got close_calls={wm.close_calls}"

    # Workspace must be restored to original
    editor_after = next((w for w in wm.windows if w.id == editor_before.id), None)
    # If window was closed, this would be None — but we asserted no close, so should exist
    assert editor_after is not None
    assert editor_after.workspace == orig_ws, f"workspace not restored: {editor_after.workspace} != {orig_ws}"

    # Maximized flag restored (unmaximize called)
    assert editor_after.maximized == 0


def test_wait_for_window_present(monkeypatch):
    """
    Fake wm returns editor after 2 polls — verifies polling logic.
    Patches time.sleep to be instant.
    """
    class PollingWM(FakeWM):
        def __init__(self):
            super().__init__(include_utility=False)
            self._polls = 0

        def find_window(self, query: str, match_title: bool = True):
            self._polls += 1
            if self._polls < 3:
                return None
            return super().find_window(query, match_title=match_title)

    wm = PollingWM()
    monkeypatch.setattr(time, "sleep", lambda *_: None)

    start = time.monotonic()
    win = wm.wait_for_window("TextEditor", timeout=5, poll_interval=0.05)
    elapsed = time.monotonic() - start

    assert win is not None, "wait_for_window should have found editor after 2 polls"
    assert win.wm_class == "org.gnome.TextEditor"
    assert wm._polls >= 3
    # Should not have timed out (elapsed < timeout)
    assert elapsed < 5

    # Also verify example.run can handle this polling WM end-to-end (smoke)
    # patch file-level `ex` (the importlib-loaded example module)

    monkeypatch.setattr(ex, "spawn_editor", lambda: None)
    # Re-create polling WM for run so poll count resets
    wm2 = PollingWM()
    demonstrated = ex.run(wm2)
    assert demonstrated >= 5, f"expected at least 5 steps with polling WM, got {demonstrated}"
