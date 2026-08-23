import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from open_alo_core.types import Point, Rect, StreamGeometry
from open_alo_core.calibration import RESIDUAL_LIMIT_PX

# --- sibling example.py loader (unique module name; folders are not packages) ---
import pathlib
import importlib.util as _ilu

def _load_example_module():
    _here = pathlib.Path(__file__).resolve().parent
    _modname = "_showcase_" + "04_calibration_workbench"
    _spec = _ilu.spec_from_file_location(_modname, _here / "example.py")
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod

_ex = _load_example_module()

gtk4_case = _ex.gtk4_case
roundtrip_error = _ex.roundtrip_error
demote_policy_demo = _ex.demote_policy_demo
fractional_scale_note = _ex.fractional_scale_note
stream_mapping_parity = _ex.stream_mapping_parity
sanitize_edge_cases = _ex.sanitize_edge_cases
run = _ex.run

ex = _ex  # loaded sibling module instance (patch THIS in tests)

# ---------------------------------------------------------------------------
# 1 — GTK4 scale is 2.0
# ---------------------------------------------------------------------------

def test_gtk4_scale_is_two():
    info = gtk4_case()
    # sx = 1854/927 = 2.0, sy = 1048/524 = 2.0
    assert abs(info["sx"] - 2.0) < 1e-6
    assert abs(info["sy"] - 2.0) < 1e-6
    # offset math: ox = x_m - sx*x_a, x_a=0 so ox = 66
    assert info["ox"] == pytest.approx(66.0, abs=1e-9)
    assert info["oy"] == pytest.approx(50.0, abs=1e-9)
    # also fields on the transform object itself
    t = info["transform"]
    assert abs(t.scale_x - 2.0) < 1e-6
    assert abs(t.scale_y - 2.0) < 1e-6
    assert t.offset_x == pytest.approx(66.0)
    assert t.offset_y == pytest.approx(50.0)
    # with perfect fit residual should be ~0 and pass
    assert info["residual"] == pytest.approx(0.0, abs=1e-9)
    assert info["passes"] is True


# ---------------------------------------------------------------------------
# 2 — residual perfect zero
# ---------------------------------------------------------------------------

def test_residual_perfect_zero():
    from open_alo_core import solve_affine, residual
    mutter = Rect(66, 50, 1854, 1048)
    atspi = Rect(0, 0, 927, 524)
    t = solve_affine(mutter, atspi)
    r = residual(mutter, atspi, t)
    assert r == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# 3 — roundtrip within 1px
# ---------------------------------------------------------------------------

def test_roundtrip_within_1px():
    info = gtk4_case()
    t = info["transform"]
    samples = [Point(0, 0), Point(10, 20), Point(100, 100), Point(463, 262), Point(926, 523)]
    err = roundtrip_error(t, samples)
    assert err <= 1
    # also direct check per-point
    for p in samples:
        back = t.inverse_point(t.transform_point(p))
        assert max(abs(back.x - p.x), abs(back.y - p.y)) <= 1


# ---------------------------------------------------------------------------
# 4 — demote policy flags drifted
# ---------------------------------------------------------------------------

def test_demote_policy_flags_drifted():
    rows = demote_policy_demo()
    # rows are (name, residual, ok_bool)
    by_name = {name: (res, ok) for name, res, ok in rows}
    assert "drifted" in by_name
    assert by_name["drifted"][1] is False  # ok == False
    assert by_name["drifted"][0] == pytest.approx(3.5)
    # perfect and gtk4 should be ok (residual < 2.0)
    assert "perfect" in by_name
    assert by_name["perfect"][1] is True
    assert by_name["perfect"][0] == pytest.approx(0.0)
    assert "gtk4_real" in by_name
    # gtk4_real residual should be ~0 < 2.0 so ok
    assert by_name["gtk4_real"][1] is True


def test_demote_policy_custom_cases():
    custom = [("a", 1.9), ("b", 2.0), ("c", 2.01)]
    rows = demote_policy_demo(custom)
    # 1.9 < 2.0 -> True, 2.0 not < 2.0 -> False, 2.01 -> False
    assert rows[0] == ("a", 1.9, True)
    assert rows[1] == ("b", 2.0, False)
    assert rows[2] == ("c", 2.01, False)


# ---------------------------------------------------------------------------
# 5 — parity true for axis-aligned
# ---------------------------------------------------------------------------

def test_parity_true_for_axis_aligned():
    sg = StreamGeometry(position=(100, 50), size=(1920, 1080), logical_size=(1920, 1080), scale=1.0)
    assert stream_mapping_parity(sg) is True


# ---------------------------------------------------------------------------
# 6 — sanitize sentinel None
# ---------------------------------------------------------------------------

def test_sanitize_sentinel_none():
    cases = sanitize_edge_cases()
    # find sentinel entry (x == INT_MIN)
    sentinel_results = [(inp, out) for inp, out in cases if inp.x == -2147483648]
    assert len(sentinel_results) == 1
    assert sentinel_results[0][1] is None

    # 1x1 -> None
    tiny_results = [(inp, out) for inp, out in cases if inp.width == 1 and inp.height == 1]
    assert len(tiny_results) == 1
    assert tiny_results[0][1] is None

    # edge 1919,1079 -> currently None (1x1 clamp filtered)
    edge = [(inp, out) for inp, out in cases if inp == Rect(1919, 1079, 2, 2)]
    assert len(edge) == 1
    # honest current behavior: may be None due to <=1 clamp
    assert edge[0][1] is None


# ---------------------------------------------------------------------------
# 7 — run offline returns 6/7 (6 pure, step 7 skipped)
# ---------------------------------------------------------------------------

def test_run_offline_counts(capsys):
    demonstrated = run(stream_info_provider=None)
    # 6 pure steps should all OK; live step skips so 6/7
    assert demonstrated == 6
    out = capsys.readouterr().out
    assert "Capabilities demonstrated: 6/7" in out
    # all 7 steps attempted (either [OK] or [SKIP])
    assert out.count("[OK]") + out.count("[SKIP]") >= 7
    # gtk4 scale message present
    assert "scale" in out.lower()


def test_run_with_mock_provider():
    sg = StreamGeometry(position=(0, 0), size=(1920, 1080), logical_size=(1536, 864), scale=1.25)
    demonstrated = run(stream_info_provider=lambda: sg)
    # with a fake provider step 7 also OK -> 7/7
    assert demonstrated == 7


def test_fractional_scale_note_structure():
    info = fractional_scale_note()
    sg = info["geometry"]
    assert sg.scale == pytest.approx(1.25)
    assert sg.logical_size == (1536, 864)
    assert sg.size == (1920, 1080)
    assert "OPEN ITEM" in info["note"] or "scale_hint" in info["note"]
    assert info["max_roundtrip_error"] <= 1
