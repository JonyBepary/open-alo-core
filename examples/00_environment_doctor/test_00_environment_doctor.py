import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
# allow `import example` from same folder
sys.path.insert(0, str(Path(__file__).resolve().parent))

# --- sibling example.py loader (unique module name; folders are not packages) ---
import pathlib
import importlib.util as _ilu

def _load_example_module():
    _here = pathlib.Path(__file__).resolve().parent
    _modname = "_showcase_" + "00_environment_doctor"
    _spec = _ilu.spec_from_file_location(_modname, _here / "example.py")
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod

_ex = _load_example_module()

check_session = _ex.check_session
check_clock = _ex.check_clock
geometry_playground = _ex.geometry_playground
sanitize_cases = _ex.sanitize_cases
keymap_samples = _ex.keymap_samples
exception_taxonomy = _ex.exception_taxonomy

ex = _ex  # loaded sibling module instance (patch THIS in tests)

from open_alo_core.types import Point, Rect


class TestSessionProbes:
    def test_structure_keys_exist(self):
        info = check_session()
        assert isinstance(info, dict)
        for key in ("session_type", "is_wayland", "portal_available", "pipewire_available"):
            assert key in info, f"missing key {key}"

    def test_booleans_types(self):
        info = check_session()
        assert info["session_type"] in ("wayland", "x11", "unknown")
        assert isinstance(info["is_wayland"], bool)
        assert isinstance(info["portal_available"], bool)
        assert isinstance(info["pipewire_available"], bool)

    def test_session_type_consistency(self):
        info = check_session()
        # is_wayland True implies session_type == wayland
        if info["is_wayland"]:
            assert info["session_type"] == "wayland"


class TestClock:
    def test_monotonic(self):
        assert check_clock() is True

    def test_monotonic_ns_increases(self):
        from open_alo_core.utils import get_monotonic_ns
        t1 = get_monotonic_ns()
        t2 = get_monotonic_ns()
        assert isinstance(t1, int)
        assert isinstance(t2, int)
        assert t2 >= t1


class TestGeometryPlayground:
    def test_contains_inclusive_true_at_edge(self):
        items = geometry_playground()
        # find the inclusive right-edge entry
        found = [r for label, r in items if "contains(Point(100,25))" in label]
        assert len(found) == 1
        assert found[0] is True

    def test_contains_inclusive_corner(self):
        items = geometry_playground()
        found = [r for label, r in items if "contains(Point(100,50))" in label]
        assert len(found) == 1
        assert found[0] is True

    def test_center_math(self):
        items = geometry_playground()
        center_entries = [r for label, r in items if "Rect(0,0,100,50).center" in label]
        assert len(center_entries) == 1
        assert center_entries[0] == Point(50, 25)

    def test_rect_edge_case_center(self):
        items = geometry_playground()
        edge_center = [r for label, r in items if "Rect(1919,1079,2,2).center" in label]
        assert len(edge_center) == 1
        # 1919 + 2//2 == 1920, 1079 + 2//2 == 1080
        assert edge_center[0] == Point(1920, 1080)

    def test_rect_edge_case_bottom_right(self):
        items = geometry_playground()
        br = [r for label, r in items if "Rect(1919,1079,2,2).bottom_right" in label]
        assert len(br) == 1
        assert br[0] == Point(1921, 1081)

    def test_size_present(self):
        items = geometry_playground()
        # Size entry should exist and have correct repr
        assert any("Size(1920,1080)" in label for label, _ in items)

    def test_rect_contains_independent(self):
        # direct API sanity without playground indirection
        r = Rect(0, 0, 10, 10)
        assert r.contains(Point(10, 10)) is True  # inclusive
        assert r.contains(Point(11, 5)) is False


class TestSanitizeCases:
    def test_int_min_none(self):
        cases = sanitize_cases()
        # first case is INT_MIN sentinel
        inp, out = cases[0]
        assert inp.x == -2147483648
        assert out is None

    def test_1x1_none(self):
        cases = sanitize_cases()
        inp, out = cases[1]
        assert inp.width == 1 and inp.height == 1
        assert out is None

    def test_clamped_width_gt_zero(self):
        cases = sanitize_cases()
        inp, out = cases[2]
        # off-screen clamp with screen_size=(1920,1080)
        assert out is not None
        assert out.width > 0 and out.height > 0
        # clamped origin should be within screen
        assert 0 <= out.x < 1920
        assert 0 <= out.y < 1080
        # right/bottom should not exceed screen
        assert out.x + out.width <= 1920
        assert out.y + out.height <= 1080

    def test_normal_passthrough(self):
        cases = sanitize_cases()
        # case index 3: normal with screen_size
        inp, out = cases[3]
        assert out == Rect(10, 20, 100, 50)
        # case index 4: same rect without screen_size
        inp2, out2 = cases[4]
        assert out2 == Rect(10, 20, 100, 50)


class TestKeymapSamples:
    def test_all_six_mappings_exact(self):
        samples = keymap_samples()
        mapping = dict(samples)
        assert mapping["enter"] == "Return"
        assert mapping["esc"] == "Escape"
        assert mapping["ctrl"] == "Control"
        assert mapping["del"] == "Delete"
        assert mapping["pageup"] == "Page_Up"
        assert mapping["unknown"] == "unknown"

    def test_passthrough_unknown(self):
        # unknown key should echo input unchanged
        samples = dict(keymap_samples())
        assert samples["unknown"] == "unknown"

    def test_count(self):
        assert len(keymap_samples()) == 6


class TestExceptionTaxonomy:
    def test_returns_non_empty_str(self):
        name = exception_taxonomy()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_is_expected_family(self):
        name = exception_taxonomy()
        # uninitialized click raises RuntimeError in current impl;
        # accept RuntimeError or any CoreError subclass
        allowed = {
            "RuntimeError",
            "InputError",
            "CoreError",
            "SessionError",
            "CaptureError",
            "PermissionDenied",
            "BackendNotAvailable",
        }
        assert name in allowed or name == "RuntimeError"

    def test_no_portal_needed(self):
        # calling again should still return same classification offline
        a = exception_taxonomy()
        b = exception_taxonomy()
        assert a == b
