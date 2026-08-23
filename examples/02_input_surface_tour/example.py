#!/usr/bin/env python3
"""
02 — Input Surface Tour
=======================

Every input injector, each guarded by geometric safety preflight.

No agent loops; a guided tour of the full UnifiedRemoteDesktop input surface.
Each injection is preceded by GeometricPreflight checks (bounds + occlusion).

Run inside your own scratch editor so injections target the focused window
without disturbing other applications.

Usage:
    python example.py              # targets whatever window has focus
    python example.py --no-spawn   # same — do not spawn a new editor window
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# --- sys.path bootstrap to parents[2]/"src" ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from open_alo_core import GeometricPreflight, UnifiedRemoteDesktop, WindowManager
from open_alo_core.types import Point, Rect, normalize_key

BANNER = "OPEN_ALO CAPABILITY SHOWCASE"
TOTAL_STEPS = 12


# ---------------------------------------------------------------------------
# Docs helpers (pure, no portal)
# ---------------------------------------------------------------------------

def key_combo_normalization_demo() -> List[Tuple[List[str], str]]:
    """
    Pure documentation of key_combo Shift-aware normalization.

    UnifiedRemoteDesktop.key_combo normalizes via normalize_key and
    lowercases bare uppercase letters when Shift is NOT in the combo,
    so ["ctrl","A"] == ["ctrl","a"].

    Returns:
        List of (combo_input, description).
    """
    return [
        (
            ["ctrl", "a"],
            'lowercase a without Shift — canonical form; already normalized',
        ),
        (
            ["ctrl", "A"],
            'uppercase A without Shift — equivalent to ["ctrl","a"] (auto-lowercased): '
            'bare uppercase letters are lowercased when no Shift in combo',
        ),
        (
            ["ctrl", "shift", "s"],
            'with Shift present, letter case is preserved — Shift-aware combo keeps "S" upper; '
            'e.g. Ctrl+Shift+S (save-as) distinguishes from Ctrl+S',
        ),
    ]


def plan_injections(
    points: List[Point],
    window_rects: Dict[int, Rect],
    z_order: List[int],
    target_win_id: int,
    stream_size: Tuple[int, int] = (1920, 1080),
) -> List[Tuple[Point, bool, str]]:
    """
    Safety gate: run BOTH preflight checks per point via GeometricPreflight().

    For each point:
      1. verify_point_bounds(pt, stream_size) — sentinel/bounds validation
      2. verify_point_occlusion(pt, win_id, window_rects, z_order) — occlusion by higher windows

    If bounds fails, occlusion is not checked (already unsafe).
    Otherwise occlusion verdict determines safety.

    Args:
        points: candidate injection points
        window_rects: {win_id: Rect}
        z_order: stacking order bottom->top
        target_win_id: window we intend to inject into
        stream_size: screen size for bounds check

    Returns:
        List of (point, verdict_is_safe, reason) — one entry per input point.
    """
    pf = GeometricPreflight(stream_size=stream_size)
    out: List[Tuple[Point, bool, str]] = []
    for pt in points:
        bv = pf.verify_point_bounds(pt, stream_size=stream_size)
        if not bv.is_safe:
            out.append((pt, False, bv.reason))
            continue
        ov = pf.verify_point_occlusion(pt, target_win_id, window_rects, z_order)
        if not ov.is_safe:
            out.append((pt, False, ov.reason))
            continue
        out.append((pt, True, ov.reason))
    return out


# ---------------------------------------------------------------------------
# Main guided tour
# ---------------------------------------------------------------------------

def run(desktop: UnifiedRemoteDesktop | None = None, wm=None) -> int:
    """
    Execute the 12-step input surface tour.

    Args:
        desktop: injected UnifiedRemoteDesktop (or MagicMock for headless tests).
                 If None, creates a real UnifiedRemoteDesktop and attempts initialize().
        wm: injected WindowManager (or MagicMock). If None, creates real WindowManager().

    Returns:
        Number of demonstrated capabilities (0..TOTAL_STEPS).
    """
    print("=" * 70)
    print(BANNER)
    print("=" * 70)
    print("02 — Input Surface Tour  |  every injector, gated by preflight")
    print("No agent loops; a guided tour of every input injector.")
    print()

    demonstrated = 0
    stream_size: Tuple[int, int] = (1920, 1080)
    own_desktop = desktop is None

    # ── Init desktop ────────────────────────────────────────────────────
    if desktop is None:
        try:
            desktop = UnifiedRemoteDesktop()
            try:
                desktop.initialize(persist_mode=2, enable_capture=False)
            except TypeError:
                # older signature without enable_capture
                try:
                    desktop.initialize(persist_mode=2)
                except Exception as e:
                    print(f"  [note] desktop initialize failed: {e}")
            except Exception as e:
                print(f"  [note] desktop initialize failed: {e}")
        except Exception as e:
            print(f"  [note] UnifiedRemoteDesktop unavailable: {e}")
            # create a minimal mock-like stub so later steps print [SKIP] not crash
            desktop = None  # type: ignore[assignment]

    if wm is None:
        try:
            wm = WindowManager()
        except Exception as e:
            print(f"  [note] WindowManager unavailable: {e}")
            wm = None

    # ── Build window map + z_order + target ─────────────────────────────
    window_rects: Dict[int, Rect] = {}
    z_order: List[int] = []
    focused = None
    target_win_id: int = 0
    target_rect: Rect | None = None
    target_center = Point(960, 540)

    if wm is not None:
        try:
            windows = wm.list_windows() if hasattr(wm, "list_windows") else []
            # windows may be MagicMock list; handle gracefully
            try:
                for w in windows:
                    try:
                        # WindowInfo has id, x, y, width, height
                        window_rects[w.id] = Rect(w.x, w.y, w.width, w.height)
                    except Exception:
                        continue
            except TypeError:
                pass
            try:
                z = wm.get_window_z_order()
                if isinstance(z, list):
                    z_order = [int(x) for x in z if isinstance(x, (int, float))]
                elif z is not None:
                    # MagicMock may return MagicMock; ignore
                    if hasattr(z, "__iter__"):
                        try:
                            z_order = [int(x) for x in list(z) if isinstance(x, (int, float))]
                        except Exception:
                            z_order = []
            except Exception:
                z_order = []
            try:
                if hasattr(wm, "get_focused_window"):
                    focused = wm.get_focused_window()
            except Exception:
                focused = None
        except Exception as e:
            print(f"  [note] window enumeration failed: {e}")

    # Attempt to get real screen size from desktop
    if desktop is not None:
        try:
            if hasattr(desktop, "get_screen_size"):
                sz = desktop.get_screen_size()
                if isinstance(sz, tuple) and len(sz) == 2:
                    stream_size = (int(sz[0]), int(sz[1]))
        except Exception:
            pass
        # also try get_stream_info for size?
        try:
            if hasattr(desktop, "get_stream_info"):
                gi = desktop.get_stream_info()
                if gi is not None and hasattr(gi, "size"):
                    stream_size = tuple(gi.size)  # type: ignore
        except Exception:
            pass

    if focused is not None:
        try:
            fid = int(getattr(focused, "id", 0))
            fx = int(getattr(focused, "x", 0))
            fy = int(getattr(focused, "y", 0))
            fw = int(getattr(focused, "width", 0))
            fh = int(getattr(focused, "height", 0))
            if fw > 1 and fh > 1:
                target_rect = Rect(fx, fy, fw, fh)
                target_center = target_rect.center
                target_win_id = fid
            else:
                # fallback to stream center
                target_center = Point(stream_size[0] // 2, stream_size[1] // 2)
                target_win_id = fid if fid else (z_order[0] if z_order else 0)
        except Exception:
            target_center = Point(stream_size[0] // 2, stream_size[1] // 2)
            target_win_id = int(getattr(focused, "id", 0)) if hasattr(focused, "id") else 0
    else:
        # no focused window — use screen center
        target_center = Point(stream_size[0] // 2, stream_size[1] // 2)
        if z_order:
            target_win_id = z_order[0]
        elif window_rects:
            target_win_id = next(iter(window_rects))
        else:
            target_win_id = 0
        # synthetic target rect for drag margins if no window
        target_rect = Rect(
            target_center.x - stream_size[0] // 4,
            target_center.y - stream_size[1] // 4,
            stream_size[0] // 2,
            stream_size[1] // 2,
        )

    # Ensure target_rect exists for drag step
    if target_rect is None:
        # derive from window_rects if available
        if target_win_id in window_rects:
            target_rect = window_rects[target_win_id]
        else:
            target_rect = Rect(
                target_center.x - 200, target_center.y - 100, 400, 200
            )

    # Helper to check preflight for a point
    def _check(pt: Point) -> Tuple[bool, str]:
        res = plan_injections([pt], window_rects, z_order, target_win_id, stream_size)
        return res[0][1], res[0][2]

    # ── Step 1: config ──────────────────────────────────────────────────
    print(f"[1/{TOTAL_STEPS}] config pause/fail_safe/touch_mode  [unified.py:1365]")
    try:
        assert desktop is not None, "desktop not initialized"
        # read current values (may be MagicMock)
        try:
            cur_pause = desktop.pause  # type: ignore[union-attr]
            cur_fail = desktop.fail_safe  # type: ignore[union-attr]
            cur_touch = desktop.touch_mode  # type: ignore[union-attr]
            # unwrap MagicMock to repr
            print(f"      before: pause={cur_pause!r} fail_safe={cur_fail!r} touch_mode={cur_touch!r}")
        except Exception:
            print("      before: <unable to read config>")
        desktop.pause = 0.03  # type: ignore[union-attr]
        # verify
        try:
            new_pause = desktop.pause  # type: ignore[union-attr]
            print(f"      [OK] pause=0.03 (was {cur_pause!r} -> now {new_pause!r})")
        except Exception:
            print("      [OK] pause set to 0.03")
        demonstrated += 1
    except Exception as e:
        print(f"      [SKIP] config: {e}")

    # ── Step 2: preflight table ─────────────────────────────────────────
    print(f"[2/{TOTAL_STEPS}] GeometricPreflight table  [preflight.py:24]")
    try:
        # center — should be safe
        safe_pt = target_center
        # corner — bounds edge case: near screen max
        corner_pt = Point(stream_size[0] - 1, stream_size[1] - 1)  # 1919,1079 on 1920x1080
        # alternative explicit 1919,1079 for doc fidelity when stream is 1920x1080
        if stream_size == (1920, 1080):
            corner_pt = Point(1919, 1079)
        # occluded demo — synthetic higher window covering a point
        occluded_pt = Point(safe_pt.x + 10, safe_pt.y + 10)
        # Build synthetic window_rects/z_order that guarantees occlusion for demo
        # Use target_win_id as lower, fake higher window 99999 on top
        fake_higher_id = 99999
        demo_rects_occluded: Dict[int, Rect] = dict(window_rects)
        # Ensure target has a rect
        if target_win_id not in demo_rects_occluded:
            demo_rects_occluded[target_win_id] = target_rect
        # Higher window covering occluded_pt
        demo_rects_occluded[fake_higher_id] = Rect(
            occluded_pt.x - 30, occluded_pt.y - 30, 100, 100
        )
        # z_order with target below higher
        if target_win_id in z_order:
            demo_z = [x for x in z_order if x != fake_higher_id] + [fake_higher_id]
            if target_win_id not in demo_z:
                demo_z = [target_win_id, fake_higher_id]
            else:
                # ensure higher is after target
                if demo_z.index(fake_higher_id) < demo_z.index(target_win_id):
                    demo_z.remove(fake_higher_id)
                    demo_z.append(fake_higher_id)
        else:
            demo_z = [target_win_id, fake_higher_id]

        r_safe = plan_injections([safe_pt], window_rects, z_order, target_win_id, stream_size)[0]
        r_corner = plan_injections([corner_pt], window_rects, z_order, target_win_id, stream_size)[0]
        r_occl = plan_injections([occluded_pt], demo_rects_occluded, demo_z, target_win_id, stream_size)[0]

        print(f"      center {safe_pt} -> is_safe={r_safe[1]} reason={r_safe[2]!r}")
        print(f"      corner {corner_pt} -> is_safe={r_corner[1]} reason={r_corner[2]!r}  (expected unsafe: sentinel/bounds)")
        print(f"      occluded {occluded_pt} (higher win {fake_higher_id}) -> is_safe={r_occl[1]} reason={r_occl[2]!r}  (expected unsafe: occluded)")
        # Demonstrate key_combo docs as part of preflight context
        for combo, desc in key_combo_normalization_demo():
            print(f"      combo {combo!r}: {desc}")
        demonstrated += 1
        print("      [OK] preflight table complete (bounds + occlusion + combo docs)")
    except Exception as e:
        print(f"      [SKIP] preflight table: {e}")

    # ── Step 3: move_mouse ──────────────────────────────────────────────
    print(f"[3/{TOTAL_STEPS}] move_mouse(Point)  [unified.py:276]")
    try:
        assert desktop is not None
        pt = target_center
        ok, reason = _check(pt)
        if not ok:
            print(f"      [SKIP] move_mouse {pt} unsafe: {reason}")
        else:
            desktop.move_mouse(pt)  # type: ignore[union-attr]
            demonstrated += 1
            print(f"      [OK] move_mouse {pt}")
    except Exception as e:
        print(f"      [SKIP] move_mouse: {e}")

    # ── Step 4: click left/right/double ─────────────────────────────────
    print(f"[4/{TOTAL_STEPS}] click(Point,button) + double_click  [unified.py:236/542] GTK4 80ms hold")
    try:
        assert desktop is not None
        pt = target_center
        ok, reason = _check(pt)
        if not ok:
            print(f"      [SKIP] click {pt} unsafe: {reason}")
        else:
            ts = desktop.click(pt, button=1)  # type: ignore[union-attr]
            print(f"      click left {pt} -> ts={ts}")
            ts2 = desktop.click(pt, button=3)  # type: ignore[union-attr]
            print(f"      click right {pt} -> ts={ts2}")
            desktop.double_click(pt, button=1)  # type: ignore[union-attr]
            print(f"      double_click {pt}")
            demonstrated += 1
            print("      [OK] click/double_click (note GTK4 max(delay,0.08) hold)")
    except Exception as e:
        print(f"      [SKIP] click: {e}")

    # ── Step 5: type_text ───────────────────────────────────────────────
    print(f"[5/{TOTAL_STEPS}] type_text(text,interval)  [unified.py:295]")
    try:
        assert desktop is not None
        pt = target_center
        ok, reason = _check(pt)
        if not ok:
            print(f"      [SKIP] type_text {pt} unsafe: {reason}")
        else:
            desktop.type_text("OPEN_ALO input tour", interval=0.01)  # type: ignore[union-attr]
            demonstrated += 1
            print('      [OK] type_text "OPEN_ALO input tour" into focused window')
    except Exception as e:
        print(f"      [SKIP] type_text: {e}")

    # ── Step 6: press_key + key_combo ───────────────────────────────────
    print(f"[6/{TOTAL_STEPS}] press_key + key_combo  [unified.py:318/349] Shift-aware")
    try:
        assert desktop is not None
        pt = target_center
        ok, reason = _check(pt)
        if not ok:
            print(f"      [SKIP] press_key {pt} unsafe: {reason}")
        else:
            desktop.press_key("Return")  # type: ignore[union-attr]
            print("      press_key Return ->", normalize_key("Return"))
            desktop.key_combo(["ctrl", "a"])  # type: ignore[union-attr]
            print('      key_combo ["ctrl","a"]')
            desktop.key_combo(["ctrl", "c"])  # type: ignore[union-attr]
            print('      key_combo ["ctrl","c"]')
            # Also demonstrate equivalence explicitly
            desktop.key_combo(["ctrl", "A"])  # type: ignore[union-attr]
            print('      key_combo ["ctrl","A"] == ["ctrl","a"] (normalized, no Shift)')
            demonstrated += 1
            print("      [OK] press_key + key_combo (Shift-aware lowercasing)")
    except Exception as e:
        print(f"      [SKIP] press_key/key_combo: {e}")

    # ── Step 7: scroll variants ─────────────────────────────────────────
    print(f"[7/{TOTAL_STEPS}] scroll/hscroll/smooth_scroll  [unified.py:389/423/443] scroll+ =up")
    try:
        assert desktop is not None
        pt = target_center
        ok, reason = _check(pt)
        if not ok:
            print(f"      [SKIP] scroll {pt} unsafe: {reason}")
        else:
            # Ensure pointer is at pt for scroll without explicit x,y
            try:
                desktop.move_mouse(pt)  # type: ignore[union-attr]
            except Exception:
                pass
            desktop.scroll(-2)  # type: ignore[union-attr]
            print("      scroll -2 (down 2 clicks)")
            desktop.scroll(2)  # type: ignore[union-attr]
            print("      scroll +2 (up 2 clicks, positive=UP)")
            desktop.hscroll(2)  # type: ignore[union-attr]
            print("      hscroll +2 (right)")
            desktop.smooth_scroll(dx=0, dy=40)  # type: ignore[union-attr]
            print("      smooth_scroll dy=40 (NotifyPointerAxis)")
            desktop.smooth_scroll(dx=0, dy=0, finish=True)  # type: ignore[union-attr]
            print("      smooth_scroll finish=True")
            demonstrated += 1
            print("      [OK] scroll variants (scroll +=up, hscroll axis1, smooth_scroll)")
    except Exception as e:
        print(f"      [SKIP] scroll: {e}")

    # ── Step 8: drag ────────────────────────────────────────────────────
    print(f"[8/{TOTAL_STEPS}] drag(start,end,button,duration)  [unified.py:461] steps=max(int(d/0.05),5)")
    try:
        assert desktop is not None
        w = target_rect.width
        h = target_rect.height
        # width*0.25 margins
        margin = max(int(w * 0.25), 20)
        start = Point(target_rect.x + margin, target_center.y)
        end = Point(target_rect.x + w - margin, target_center.y)
        # Clamp to stream bounds
        start = Point(max(0, min(start.x, stream_size[0] - 1)), max(0, min(start.y, stream_size[1] - 1)))
        end = Point(max(0, min(end.x, stream_size[0] - 1)), max(0, min(end.y, stream_size[1] - 1)))
        ok, reason = _check(start)
        if not ok:
            print(f"      [SKIP] drag start {start} unsafe: {reason}")
        else:
            ok2, reason2 = _check(end)
            if not ok2:
                print(f"      [SKIP] drag end {end} unsafe: {reason2}")
            else:
                desktop.drag(start, end, button=1, duration=0.3)  # type: ignore[union-attr]
                demonstrated += 1
                print(f"      [OK] drag {start} -> {end} duration=0.3 interpolated")
    except Exception as e:
        print(f"      [SKIP] drag: {e}")

    # ── Step 9: swipe ───────────────────────────────────────────────────
    print(f"[9/{TOTAL_STEPS}] swipe(start,end,duration=0.3,steps=10)  [unified.py:494]")
    try:
        assert desktop is not None
        start = target_center
        end = Point(target_center.x, min(target_center.y + 100, stream_size[1] - 1))
        ok, reason = _check(start)
        if not ok:
            print(f"      [SKIP] swipe {start} unsafe: {reason}")
        else:
            desktop.swipe(start, end, duration=0.3, steps=10)  # type: ignore[union-attr]
            demonstrated += 1
            print(f"      [OK] swipe downward {start} -> {end}")
    except Exception as e:
        print(f"      [SKIP] swipe: {e}")

    # ── Step 10: hold_key Shift+click ───────────────────────────────────
    print(f"[10/{TOTAL_STEPS}] hold_key Shift + click  [unified.py:528] contextmanager")
    try:
        assert desktop is not None
        pt = Point(min(target_center.x + 10, stream_size[0] - 1), target_center.y)
        ok, reason = _check(pt)
        if not ok:
            print(f"      [SKIP] hold_key {pt} unsafe: {reason}")
        else:
            with desktop.hold_key("Shift"):  # type: ignore[union-attr]
                desktop.click(pt, button=1)  # type: ignore[union-attr]
            demonstrated += 1
            print(f"      [OK] hold_key Shift + click {pt}")
    except Exception as e:
        print(f"      [SKIP] hold_key: {e}")

    # ── Step 11: move_mouse_relative ────────────────────────────────────
    print(f"[11/{TOTAL_STEPS}] move_mouse_relative(dx,dy)  [unified.py:552]")
    try:
        assert desktop is not None
        # Use target_center as preflight proxy
        pt = target_center
        ok, reason = _check(pt)
        if not ok:
            print(f"      [SKIP] move_mouse_relative proxy {pt} unsafe: {reason}")
        else:
            desktop.move_mouse_relative(15, 15)  # type: ignore[union-attr]
            time.sleep(0.05)
            desktop.move_mouse_relative(-15, -15)  # type: ignore[union-attr]
            demonstrated += 1
            print("      [OK] move_mouse_relative +15,+15 then -15,-15")
    except Exception as e:
        print(f"      [SKIP] move_mouse_relative: {e}")

    # ── Step 12: press_keys ─────────────────────────────────────────────
    print(f"[12/{TOTAL_STEPS}] press_keys(keys)  [unified.py:569]")
    try:
        assert desktop is not None
        pt = target_center
        ok, reason = _check(pt)
        if not ok:
            print(f"      [SKIP] press_keys {pt} unsafe: {reason}")
        else:
            desktop.press_keys(["o", "p", "e", "n"])  # type: ignore[union-attr]
            demonstrated += 1
            print('      [OK] press_keys ["o","p","e","n"]')
    except Exception as e:
        print(f"      [SKIP] press_keys: {e}")

    print()
    print("-" * 70)
    print(f"Capabilities demonstrated: {demonstrated}/{TOTAL_STEPS}")
    print("-" * 70)
    if demonstrated == TOTAL_STEPS:
        print("All 12 input injectors live — full surface tour complete.")
    elif demonstrated == 0:
        print("No portal available — running headless or permission denied (see README).")
    else:
        print("Partial tour — check [SKIP] lines above for reasons.")
    print()
    return demonstrated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="02 Input Surface Tour — every injector, gated by preflight",
        epilog="Default targets whatever window has focus — run inside your own scratch editor.",
    )
    parser.add_argument(
        "--no-spawn",
        action="store_true",
        help="Do not spawn a scratch editor window; target the currently focused window",
    )
    args = parser.parse_args()

    # --no-spawn is the default behavior (we never spawn); flag is accepted for compatibility
    if args.no_spawn:
        print("[note] --no-spawn: targeting focused window (no editor spawned)")

    try:
        run()
        return 0
    except KeyboardInterrupt:
        print("\n[interrupt] cancelled by user (Ctrl+C)")
        return 130
    except Exception as e:
        print(f"\n[error] unexpected: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
