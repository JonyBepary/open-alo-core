"""
Headless tests for 05_legacy_backends_compare — no portal, no Wayland.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Bootstrap same as ex.py — parents[2]/"src" + local dir for `import example`
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

# sibling module loaded above as `ex`
# --- sibling ex.py loader (unique module name; folders are not packages) ---
import pathlib
import importlib.util as _ilu

def _load_example_module():
    _here = pathlib.Path(__file__).resolve().parent
    _modname = "_showcase_" + "05_legacy_backends_compare"
    _spec = _ilu.spec_from_file_location(_modname, _here / "example.py")
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod

_ex = _load_example_module()

capture_once = _ex.capture_once
comparison_table = _ex.comparison_table
input_probe = _ex.input_probe

ex = _ex  # loaded sibling module instance (patch THIS in tests)



def test_comparison_rows_cover_three_backends():
    rows = comparison_table()
    assert len(rows) >= 4, f"expected >=4 rows, got {len(rows)}"
    for row in rows:
        # row is (aspect, legacy, unified) — across cells all three names must appear
        joined = " ".join(str(c) for c in row)
        assert "WaylandCapture" in joined, f"row missing WaylandCapture: {row}"
        assert "WaylandInput" in joined, f"row missing WaylandInput: {row}"
        assert "UnifiedRemoteDesktop" in joined, f"row missing UnifiedRemoteDesktop: {row}"


def test_capture_once_handles_failure(monkeypatch):
    # monkeypatch WaylandCapture.capture_screen to raise -> capture_once returns None
    def _raise(*args, **kwargs):
        raise RuntimeError("portal denied")

    monkeypatch.setattr(ex.WaylandCapture, "capture_screen", _raise)
    result = capture_once()
    assert result is None


def test_input_probe_false_without_portal(monkeypatch):
    # monkeypatch WaylandInput.initialize -> False -> probe should return False
    monkeypatch.setattr(ex.WaylandInput, "initialize", lambda self, persist_mode=0: False)
    # ensure key_combo not called (or stub it)
    monkeypatch.setattr(ex.WaylandInput, "key_combo", lambda self, keys: None)
    monkeypatch.setattr(ex.WaylandInput, "close", lambda self: None)
    result = input_probe(keys=["ctrl", "l"])
    assert result is False


def test_table_printable():
    rows = comparison_table()
    lines = ex._format_table(rows)
    assert len(lines) >= 4
    for line in lines:
        assert len(line) <= 120, f"line too wide ({len(line)}): {line!r}"
    # also check run footer is headless-safe
    demonstrated = ex.run(skip_live=True, with_input=False)
    assert 0 <= demonstrated <= ex.TOTAL_STEPS
