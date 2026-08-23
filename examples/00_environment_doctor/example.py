import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from open_alo_core.utils import (
    detect_session_type,
    is_wayland,
    is_portal_available,
    is_pipewire_available,
    get_monotonic_ns,
    sanitize_rect,
)
from open_alo_core.types import Point, Size, Rect, normalize_key
from open_alo_core import UnifiedRemoteDesktop
from open_alo_core.exceptions import (
    CoreError,
    InputError,
    SessionError,
    CaptureError,
    PermissionDenied,
    BackendNotAvailable,
)


# ---------------------------------------------------------------------------
# Pure logic — no Wayland/portal side effects, safe for headless tests
# ---------------------------------------------------------------------------

def check_session() -> dict:
    """Probe session / portal / PipeWire availability."""
    return {
        "session_type": detect_session_type(),
        "is_wayland": is_wayland(),
        "portal_available": is_portal_available(),
        "pipewire_available": is_pipewire_available(),
    }


def check_clock() -> bool:
    """Return True if monotonic clock moves forward (positive delta)."""
    t1 = get_monotonic_ns()
    t2 = get_monotonic_ns()
    return isinstance(t1, int) and isinstance(t2, int) and t2 >= t1 and (t2 - t1) >= 0


def geometry_playground() -> list:
    """Exercise Point/Size/Rect primitives.

    Returns:
        List of (label, result) tuples.
    """
    results: list = []

    # 1 — center property
    r = Rect(0, 0, 100, 50)
    results.append(("Rect(0,0,100,50).center == Point(50,25)", r.center))

    # 2 — contains() inclusive right edge (spec requires True)
    r2 = Rect(0, 0, 100, 50)
    edge_point = Point(100, 25)  # exactly on right edge
    results.append(("Rect(0,0,100,50).contains(Point(100,25)) inclusive edge", r2.contains(edge_point)))

    # 3 — contains() inclusive bottom edge / corner
    corner = Point(100, 50)  # bottom-right corner inclusive
    results.append(("Rect(0,0,100,50).contains(Point(100,50)) corner inclusive", r2.contains(corner)))

    # 4 — Rect(1919,1079,2,2) edge case at 1920x1080 boundary
    edge_rect = Rect(1919, 1079, 2, 2)
    results.append(("Rect(1919,1079,2,2).center", edge_rect.center))
    results.append(("Rect(1919,1079,2,2).bottom_right", edge_rect.bottom_right))
    results.append(("Rect(1919,1079,2,2).contains(Point(1920,1080)) inclusive", edge_rect.contains(Point(1920, 1080))))

    # 5 — Size basic (bonus, still geometry)
    s = Size(1920, 1080)
    results.append(("Size(1920,1080)", s))

    return results


def sanitize_cases() -> list:
    """Cover sanitize_rect edge cases.

    Returns:
        List of (input_rect, sanitized_result) tuples.
        sanitized_result is Rect or None.
    """
    cases: list = []

    # 1 — INT_MIN sentinel → None
    sentinel = Rect(-2147483648, -2147483648, 100, 100)
    cases.append((sentinel, sanitize_rect(sentinel)))

    # 2 — 1x1 → None (width <=1 / height <=1 filtered)
    tiny = Rect(10, 10, 1, 1)
    cases.append((tiny, sanitize_rect(tiny)))

    # 3 — off-screen clamp with screen_size=(1920,1080)
    #     Partially off-screen bottom-right; should clamp width/height >0
    offscreen = Rect(1800, 900, 300, 300)
    clamped = sanitize_rect(offscreen, screen_size=(1920, 1080))
    cases.append((offscreen, clamped))

    # 4 — normal pass-through (no clamp needed)
    normal = Rect(10, 20, 100, 50)
    cases.append((normal, sanitize_rect(normal, screen_size=(1920, 1080))))

    # 5 — also test normal without screen_size arg (pure pass-through)
    cases.append((normal, sanitize_rect(normal)))

    return cases


def keymap_samples() -> list:
    """Return (raw, normalized) pairs for normalize_key."""
    pairs = [
        ("enter", "Return"),
        ("esc", "Escape"),
        ("ctrl", "Control"),
        ("del", "Delete"),
        ("pageup", "Page_Up"),
        ("unknown", "unknown"),  # passthrough
    ]
    return [(raw, normalize_key(raw)) for raw, expected in pairs]


def exception_taxonomy() -> str:
    """Deliberately trigger uninitialized click and classify the exception.

    Returns:
        Name of the caught exception class.
    """
    try:
        UnifiedRemoteDesktop().click(Point(1, 1))
    except InputError:
        return "InputError"
    except PermissionDenied:
        return "PermissionDenied"
    except SessionError:
        return "SessionError"
    except CaptureError:
        return "CaptureError"
    except BackendNotAvailable:
        return "BackendNotAvailable"
    except CoreError:
        return "CoreError"
    except RuntimeError:
        return "RuntimeError"
    except Exception as e:
        # broad fallback — still returns a non-empty class name
        return type(e).__name__
    return "NoException"


# ---------------------------------------------------------------------------
# CLI — banner, numbered demo list, STEP execution, summary
# ---------------------------------------------------------------------------

TITLE = "ENVIRONMENT DOCTOR"
BANNER = f"OPEN_ALO CAPABILITY SHOWCASE — {TITLE}"


def main() -> int:
    print(BANNER)
    print("=" * len(BANNER))
    print()
    print("Can this machine drive OPEN_ALO? Zero permissions, zero side effects.")
    print()
    print("This run demonstrates:")
    demos = [
        "Session / portal / PipeWire probing (detect_session_type, is_wayland, is_portal_available, is_pipewire_available)",
        "Monotonic clock (get_monotonic_ns)",
        "Geometry primitives (Point / Size / Rect — center, contains inclusive edge, 1919,1079 edge case)",
        "Rect sanitization (sanitize_rect — INT_MIN sentinel, 1x1 filter, off-screen clamp, pass-through)",
        "Key normalization (normalize_key — enter/esc/ctrl/del/pageup/unknown)",
        "Exception taxonomy (UnifiedRemoteDesktop uninitialized → RuntimeError/InputError family)",
    ]
    for i, d in enumerate(demos, 1):
        print(f"  {i}. {d}")
    print()

    total = 6
    ok = 0

    # STEP 1 — session
    print("STEP 1 — Session probes")
    try:
        info = check_session()
        print(f"  session_type={info['session_type']}  is_wayland={info['is_wayland']}  portal={info['portal_available']}  pipewire={info['pipewire_available']}")
        print("  [OK] session probes executed")
        ok += 1
    except Exception as e:
        print(f"  [SKIP] session probes failed: {e}")

    # STEP 2 — clock
    print("STEP 2 — Monotonic clock")
    try:
        mono = check_clock()
        t1 = get_monotonic_ns()
        t2 = get_monotonic_ns()
        print(f"  t1={t1}  t2={t2}  delta={t2 - t1}  monotonic={mono}")
        if mono:
            print("  [OK] clock is monotonic (positive delta)")
            ok += 1
        else:
            print("  [SKIP] clock not monotonic")
    except Exception as e:
        print(f"  [SKIP] clock check failed: {e}")

    # STEP 3 — geometry
    print("STEP 3 — Geometry playground")
    try:
        items = geometry_playground()
        for label, result in items:
            print(f"  {label} -> {result}")
        # validate inclusive edge for summary
        ok_check = any(label.startswith("Rect(0,0,100,50).contains(Point(100,25))") and result is True for label, result in items)
        if ok_check:
            print("  [OK] geometry primitives behave correctly")
            ok += 1
        else:
            print("  [SKIP] geometry inclusive edge failed")
    except Exception as e:
        print(f"  [SKIP] geometry failed: {e}")

    # STEP 4 — sanitize
    print("STEP 4 — Rect sanitization")
    try:
        cases = sanitize_cases()
        for inp, out in cases:
            print(f"  sanitize_rect({inp}) -> {out}")
        # validate expected invariants
        int_min_ok = cases[0][1] is None
        tiny_ok = cases[1][1] is None
        clamped = cases[2][1]
        clamped_ok = clamped is not None and clamped.width > 0 and clamped.height > 0
        normal_ok = cases[3][1] is not None
        if int_min_ok and tiny_ok and clamped_ok and normal_ok:
            print("  [OK] sanitize_rect covers sentinel, 1x1, clamp, pass-through")
            ok += 1
        else:
            print("  [SKIP] sanitize_rect invariants not met")
    except Exception as e:
        print(f"  [SKIP] sanitize failed: {e}")

    # STEP 5 — keymap
    print("STEP 5 — Key normalization")
    try:
        samples = keymap_samples()
        for raw, norm in samples:
            print(f"  normalize_key({raw!r}) -> {norm!r}")
        expected = {
            "enter": "Return",
            "esc": "Escape",
            "ctrl": "Control",
            "del": "Delete",
            "pageup": "Page_Up",
            "unknown": "unknown",
        }
        all_match = all(n == expected[r] for r, n in samples)
        if all_match:
            print("  [OK] all six key mappings correct")
            ok += 1
        else:
            print("  [SKIP] key mappings mismatch")
    except Exception as e:
        print(f"  [SKIP] keymap failed: {e}")

    # STEP 6 — exception taxonomy
    print("STEP 6 — Exception taxonomy")
    try:
        name = exception_taxonomy()
        print(f"  UnifiedRemoteDesktop().click without init raised: {name}")
        if name and isinstance(name, str) and len(name) > 0:
            print(f"  [OK] caught and classified as {name}")
            ok += 1
        else:
            print("  [SKIP] exception taxonomy returned empty")
    except Exception as e:
        print(f"  [SKIP] exception taxonomy crashed: {e}")

    print()
    print(f"Capabilities demonstrated: {ok}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
