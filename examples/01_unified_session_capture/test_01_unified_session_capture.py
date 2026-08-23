"""
Headless tests for 01_unified_session_capture — no portal, no Wayland.

Uses a MagicMock desktop injected into example.run(desktop=...).
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Bootstrap same as example.py — parents[2]/"src" + local dir for `import example`
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from open_alo_core import create_unified_desktop  # noqa: E402
from open_alo_core.types import StreamGeometry  # noqa: E402

# --- sibling example.py loader (unique module name; folders are not packages) ---
import pathlib
import importlib.util as _ilu

def _load_example_module():
    _here = pathlib.Path(__file__).resolve().parent
    _modname = "_showcase_" + "01_unified_session_capture"
    _spec = _ilu.spec_from_file_location(_modname, _here / "example.py")
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod

_ex = _load_example_module()

describe_stream = _ex.describe_stream
raw_to_image_shape = _ex.raw_to_image_shape
run = _ex.run

ex = _ex  # loaded sibling module instance (patch THIS in tests)



# ---------------------------------------------------------------------------
# Fixture: fake_desktop with realistic returns
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_desktop() -> MagicMock:
    m = MagicMock()

    geom = StreamGeometry(
        position=(0, 0),
        size=(1920, 1080),
        scale=1.25,
        node_id=42,
        source_type=1,
    )
    # logical_size is auto-derived when omitted? StreamGeometry default is (1920,1080)
    # but to match spec we ensure logical_size reflects scale: round(1920/1.25)=1536, 1080/1.25=864
    # However StreamGeometry dataclass stores what we pass; get_stream_info() helper
    # does the rounding. For the mock we set explicit logical_size to match expectation.
    # The spec says fixture size=(1920,1080) scale=1.25 — logical_size should be (1536,864).
    # To keep the fake realistic, override logical_size accordingly.
    object.__setattr__(geom, "logical_size", (1536, 864))

    m.get_screen_size.return_value = (1920, 1080)
    m.get_stream_info.return_value = geom
    m.capture_screenshot.return_value = b"\x89PNG\r\n\x1a\nfake"
    m.get_frame.return_value = b"\x89PNG frame"
    m.get_frame_rgb.return_value = {
        "buffer": bytes(12 * 12 * 4),
        "width": 12,
        "height": 12,
        "stride": 48,
        "timestamp_ns": 999,
        "stream_info": geom,
    }
    m.capture_observation.return_value = {
        "png": b"\x89PNG",
        "timestamp_ns": 123,
        "stream_info": geom,
        "screen_size": (1920, 1080),
    }
    m.capture_raw_rgb.return_value = {
        "buffer": bytes(12 * 12 * 4),
        "width": 12,
        "height": 12,
        "stride": 48,
        "timestamp_ns": 456,
        "stream_info": geom,
    }
    m.initialize.return_value = True
    m.close.return_value = None
    # _ensure_raw_pipeline is optional but mocked for completeness
    m._ensure_raw_pipeline.return_value = None

    return m


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_describe_stream_typed_and_compat(fake_desktop):
    geom = fake_desktop.get_stream_info()
    fields = describe_stream(geom)
    # Convert to dict for easy lookup (last occurrence wins)
    d = {k: v for k, v in fields}

    # Typed access should have scale 1.25
    assert d["scale (typed)"] == pytest.approx(1.25)
    assert d["scale (compat [])"] == pytest.approx(1.25)

    # Legacy compat via [] and .get
    assert d["position (compat [])"] == (0, 0)
    assert d["node_id (compat .get)"] == 42

    # Verify typed logical_size present
    assert "logical_size (typed)" in d
    assert d["logical_size (typed)"] == (1536, 864)

    # Verify source_type compat
    assert d["source_type (compat .get)"] == 1

    # Ensure both access styles were exercised (keys present)
    assert any("typed" in k for k, _ in fields)
    assert any("compat" in k for k, _ in fields)


def test_raw_shape_math():
    # stride 48, w 12, h 12 -> (12,12,3)
    buf = bytes(12 * 12 * 4)  # actually stride*h = 48*12 = 576 bytes; 12*12*4 also 576
    # Ensure length matches stride*h
    assert len(buf) == 48 * 12
    shape = raw_to_image_shape(buf, 12, 48)
    assert shape == (12, 12, 3)

    # Additional sanity: different dimensions
    buf2 = bytes(10 * 64)  # h=10, stride=64
    assert raw_to_image_shape(buf2, 16, 64) == (10, 16, 3)  # w=16 -> w*3=48 <= stride 64 (padding 16)

    # Edge: zero stride
    assert raw_to_image_shape(b"", 10, 0) == (0, 10, 3)


def test_run_counts_steps(fake_desktop, capsys):
    demonstrated = run(fake_desktop)

    # Should demonstrate at least 6 of 8 with the fake
    assert demonstrated >= 6, f"expected >=6, got {demonstrated}"
    assert demonstrated <= 8

    out = capsys.readouterr().out
    # Footer present
    assert "Capabilities demonstrated:" in out
    assert f"{demonstrated}/8" in out or f"{demonstrated} / 8" in out or f"{demonstrated}/" in out

    # Verify all 8 steps were attempted (either [OK] or [SKIP] lines)
    # Count [OK] / [SKIP] markers — at least 8 markers total
    assert out.count("[OK]") + out.count("[SKIP]") >= 8

    # Verify get_frame was called paced loop (at least once, ideally 5)
    assert fake_desktop.get_frame.call_count >= 1
    # Accept 5 but be lenient: mock may be called 5 times
    # The spec says assert call_count>=1 is fine
    # Also check other key methods were invoked
    assert fake_desktop.get_screen_size.called
    assert fake_desktop.get_stream_info.called
    assert fake_desktop.capture_screenshot.called
    assert fake_desktop.capture_observation.called
    assert fake_desktop.capture_raw_rgb.called
    assert fake_desktop.close.called


def test_factory_exists():
    assert callable(create_unified_desktop)
    # Signature check: should accept persist_mode and enable_capture
    import inspect

    sig = inspect.signature(create_unified_desktop)
    params = list(sig.parameters.keys())
    assert "persist_mode" in params
    assert "enable_capture" in params
