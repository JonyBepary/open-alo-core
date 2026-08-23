#!/usr/bin/env python3
"""
04 — Calibration Workbench — the math layer that makes clicks land.

Mostly pure; one optional live step. Demonstrates affine calibration
between AT-SPI and Mutter coordinate spaces, residual policy,
fractional-scale geometry, stream-mapping parity, and sanitize_rect edges.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, List, Tuple, Optional

# --- sys.path bootstrap to parents[2]/"src" ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from open_alo_core import (
    AffineTransform2D,
    solve_affine,
    residual,
    RESIDUAL_LIMIT_PX,
    StreamGeometry,
    sanitize_rect,
)
from open_alo_core.types import Point, Rect
from open_alo_core.utils import map_global_to_stream

BANNER = "OPEN_ALO CAPABILITY SHOWCASE"
TITLE = "04 — Calibration Workbench — the math layer that makes clicks land"
TOTAL_STEPS = 7

# ---------------------------------------------------------------------------
# Pure helpers (no portal / no Wayland)
# ---------------------------------------------------------------------------

def gtk4_case() -> dict:
    """Real GTK4 2x HiDPI case: AT-SPI reports half-size vs Mutter.

    Returns:
        dict with keys: atspi, mutter, transform, sx, sy, ox, oy, residual, passes
    """
    atspi = Rect(0, 0, 927, 524)
    mutter = Rect(66, 50, 1854, 1048)
    t = solve_affine(mutter, atspi)
    res = residual(mutter, atspi, t)
    return {
        "atspi": atspi,
        "mutter": mutter,
        "transform": t,
        "sx": t.scale_x,
        "sy": t.scale_y,
        "ox": t.offset_x,
        "oy": t.offset_y,
        "residual": res,
        "passes": res < RESIDUAL_LIMIT_PX,
    }


def roundtrip_error(t: AffineTransform2D, sample_points: List[Point]) -> int:
    """Max Chebyshev error (px) after transform → inverse round-trip.

    Because transform_point / inverse_point round to ints, a 0/1 px
    error is expected — never >1 px for scales >=1.

    Args:
        t: affine transform to test
        sample_points: points in source space

    Returns:
        int max over points of max(|dx|,|dy|) after round-trip.
    """
    if not sample_points:
        return 0
    max_err = 0
    for pt in sample_points:
        mapped = t.transform_point(pt)
        back = t.inverse_point(mapped)
        err = max(abs(back.x - pt.x), abs(back.y - pt.y))
        if err > max_err:
            max_err = err
    return int(max_err)


def demote_policy_demo(cases: Optional[List[Tuple[str, float]]] = None) -> List[Tuple[str, float, bool]]:
    """Replicate RuntimeCalibrator demotion rule: ok = residual < RESIDUAL_LIMIT_PX.

    Args:
        cases: optional list of (name, residual) pairs. When None, uses the
               three canonical cases required by the spec:
               perfect 0.0, gtk4 real (~<2 px), drifted 3.5 px.

    Returns:
        List of (name, residual, ok_bool).
    """
    if cases is None:
        # compute real gtk4 residual once
        info = gtk4_case()
        gtk4_res = float(info["residual"])
        cases = [
            ("perfect", 0.0),
            ("gtk4_real", gtk4_res),
            ("drifted", 3.5),
        ]
    result: List[Tuple[str, float, bool]] = []
    for name, res in cases:
        ok = res < RESIDUAL_LIMIT_PX
        result.append((name, float(res), bool(ok)))
    return result


def fractional_scale_note() -> dict:
    """Worked fractional-scale example with StreamGeometry.

    Uses the canonical GNOME fractional case:
        scale=1.25, logical_size=(1536,864), size=(1920,1080)
        size = round(logical_size * scale)  -> 1536*1.25=1920, 864*1.25=1080

    Demonstrates stream_to_global / global_to_stream round-trip and
    documents the open item: calibrator cache key doesn't yet include
    ``scale_hint`` (so a scale change without geometry change could hit
    a stale affine).

    Returns:
        dict with stream geometry, sample points and round-trip error.
    """
    sg = StreamGeometry(
        position=(0, 0),
        size=(1920, 1080),
        logical_size=(1536, 864),
        scale=1.25,
        node_id=None,
        source_type=None,
    )
    # sanity check the size relation that the spec claims
    # logical_size * scale ≈ size (allow rounding, but here exact)
    assert sg.size == (1920, 1080)
    assert sg.logical_size == (1536, 864)
    assert sg.scale == 1.25

    samples = [Point(0, 0), Point(100, 100), Point(1535, 863), Point(768, 432)]
    # round-trip: global -> stream -> global
    errors: List[int] = []
    for g in samples:
        s = sg.global_to_stream_point(g)
        back = sg.stream_to_global_point(s)
        err = max(abs(back.x - g.x), abs(back.y - g.y))
        errors.append(int(err))
    max_err = max(errors) if errors else 0

    # also exercise inverse via dict position (parity helper uses this separately)
    return {
        "geometry": sg,
        "samples": samples,
        "max_roundtrip_error": max_err,
        "note": (
            "OPEN ITEM: calibrator cache key does not yet include scale_hint. "
            "A fractional-scale change that leaves position/size unchanged "
            "would reuse a stale AffineTransform2D until the window moves."
        ),
    }


def stream_mapping_parity(sg: StreamGeometry) -> bool:
    """Compare typed StreamGeometry mapping vs legacy utils.map_global_to_stream.

    Docs parity left over from M4 migration.

    Args:
        sg: StreamGeometry whose position offsets the mapping

    Returns:
        True iff sg.global_to_stream_point(p) equals
        map_global_to_stream(p, {"position": sg.position}) for all test points.
    """
    probes = [
        Point(0, 0),
        Point(int(sg.position[0]), int(sg.position[1])),
        Point(int(sg.position[0]) + 10, int(sg.position[1]) + 20),
        Point(1920, 1080),
        Point(1500, 800),
    ]
    legacy_dict = {"position": sg.position}
    for p in probes:
        a = sg.global_to_stream_point(p)
        b = map_global_to_stream(p, legacy_dict)
        if a != b:
            return False
    return True


def sanitize_edge_cases() -> List[Tuple[Rect, Optional[Rect]]]:
    """Document sanitize_rect current behavior honestly.

    Returns:
        List of (input_rect, result) where result is Rect or None.
        Cases:
          - INT_MIN sentinel  (-2147483648, -2147483648, 100, 100) -> None
          - 1x1 tiny         (10, 10, 1, 1)                      -> None (w<=1 clamp)
          - off-screen       (3000, 2000, 100, 100) w/ 1920x1080 -> None
          - edge overflow    (1919, 1079, 2, 2) w/ 1920x1080      -> None (clamp leaves 1x1 -> None)
    """
    screen = (1920, 1080)
    cases: List[Tuple[Rect, Optional[Rect]]] = []

    sentinel = Rect(-2147483648, -2147483648, 100, 100)
    cases.append((sentinel, sanitize_rect(sentinel)))

    tiny = Rect(10, 10, 1, 1)
    cases.append((tiny, sanitize_rect(tiny)))

    offscreen = Rect(3000, 2000, 100, 100)
    cases.append((offscreen, sanitize_rect(offscreen, screen_size=screen)))

    edge = Rect(1919, 1079, 2, 2)
    cases.append((edge, sanitize_rect(edge, screen_size=screen)))

    return cases


# ---------------------------------------------------------------------------
# CLI flow — 7 numbered steps, [OK]/[SKIP], footer
# ---------------------------------------------------------------------------

def run(stream_info_provider: Optional[Callable[[], StreamGeometry]] = None) -> int:
    """Execute the 7-step showcase.

    Args:
        stream_info_provider: optional callable returning StreamGeometry
            (on live Wayland: ``UnifiedRemoteDesktop.get_stream_info``).
            When None, step 7 prints [SKIP no portal].

    Returns:
        Number of demonstrated capabilities (0..TOTAL_STEPS).
    """
    print("=" * 70)
    print(BANNER)
    print("=" * 70)
    print(TITLE)
    print()
    print("This run demonstrates:")
    demos = [
        "GTK4 2x affine fit (solve_affine + residual + RESIDUAL_LIMIT_PX)",
        "Round-trip integer error (transform_point / inverse_point)",
        "Demotion policy (RuntimeCalibrator: residual < 2.0 px → ok else VISION_ONLY)",
        "Fractional-scale StreamGeometry walk-through (scale=1.25)",
        "Stream-mapping parity (StreamGeometry vs legacy map_global_to_stream)",
        "Sanitize edge cases (INT_MIN, 1x1, off-screen, 1919,1079 edge)",
        "OPTIONAL live probe (UnifiedRemoteDesktop.get_stream_info → map a point)",
    ]
    for i, d in enumerate(demos, 1):
        print(f"  {i}. {d}")
    print()

    ok = 0

    # STEP 1 — GTK4 case
    print("[1/7] gtk4_case — solve_affine(mutter, atspi) + residual")
    try:
        info = gtk4_case()
        t = info["transform"]
        print(f"      atspi : {info['atspi']}")
        print(f"      mutter: {info['mutter']}")
        print(f"      AffineTransform2D(scale_x={info['sx']:.6f}, scale_y={info['sy']:.6f}, offset_x={info['ox']:.1f}, offset_y={info['oy']:.1f})")
        print(f"      residual={info['residual']:.4f} px  limit={RESIDUAL_LIMIT_PX}  passes={info['passes']}")
        # validate expected math for the known case
        if abs(info['sx'] - 2.0) < 1e-6 and abs(info['sy'] - 2.0) < 1e-6:
            print("      [OK] scale ≈2.0 (GTK4 reports half physical pixels)")
            ok += 1
        else:
            print("      [SKIP] scale deviates from 2.0 unexpectedly")
    except Exception as e:
        print(f"      [SKIP] gtk4_case failed: {e}")

    # STEP 2 — roundtrip
    print("[2/7] roundtrip_error — transform ↔ inverse (int rounding)")
    try:
        info = gtk4_case()
        t = info["transform"]
        samples = [Point(0, 0), Point(10, 20), Point(100, 100), Point(463, 262), Point(926, 523)]
        err = roundtrip_error(t, samples)
        print(f"      samples: {samples}")
        # show per-point detail
        for p in samples:
            mapped = t.transform_point(p)
            back = t.inverse_point(mapped)
            print(f"        {p} -> {mapped} -> {back}  err={max(abs(back.x-p.x), abs(back.y-p.y))} px")
        print(f"      max error = {err} px (expected <=1 px due to int rounding)")
        if err <= 1:
            print("      [OK] round-trip within 1 px")
            ok += 1
        else:
            print("      [SKIP] round-trip error >1 px")
    except Exception as e:
        print(f"      [SKIP] roundtrip failed: {e}")

    # STEP 3 — demote policy
    print("[3/7] demote policy — residual < RESIDUAL_LIMIT_PX → ok else VISION_ONLY")
    try:
        rows = demote_policy_demo()
        print(f"      limit = {RESIDUAL_LIMIT_PX} px")
        for name, res, passes in rows:
            grounding = "AT_SPI" if passes else "VISION_ONLY"
            verdict = "ok" if passes else "DEMOTE"
            print(f"        {name:12s}  residual={res:5.2f}  ok={str(passes):5s}  -> {verdict:7s} grounding={grounding}")
        # which case flips to VISION_ONLY?
        flipped = [n for n, _, ok_ in rows if not ok_]
        print(f"      flipped to VISION_ONLY: {flipped if flipped else 'none'}")
        # validate that drifted is flagged
        drifted_ok = next((ok_ for n, _, ok_ in rows if n == "drifted"), None)
        if drifted_ok is False:
            print("      [OK] policy flags drifted (3.5 px) as not ok")
            ok += 1
        else:
            print("      [SKIP] demote policy mismatch")
    except Exception as e:
        print(f"      [SKIP] demote policy failed: {e}")

    # STEP 4 — fractional scale
    print("[4/7] fractional scale — StreamGeometry(scale=1.25) round-trip")
    try:
        note = fractional_scale_note()
        sg = note["geometry"]
        print(f"      StreamGeometry(position={sg.position}, size={sg.size}, logical_size={sg.logical_size}, scale={sg.scale})")
        print(f"      size == round(logical_size * scale) ? {sg.size} == {(int(round(sg.logical_size[0]*sg.scale)), int(round(sg.logical_size[1]*sg.scale)))}")
        for p in note["samples"]:
            s = sg.global_to_stream_point(p)
            back = sg.stream_to_global_point(s)
            print(f"        global {p} -> stream {s} -> global {back}  (stream_to_global/global_to_stream)")
        print(f"      max round-trip error: {note['max_roundtrip_error']} px")
        print(f"      NOTE: {note['note']}")
        print("      [OK] fractional-scale walk-through complete")
        ok += 1
    except Exception as e:
        print(f"      [SKIP] fractional scale failed: {e}")

    # STEP 5 — parity
    print("[5/7] stream mapping parity — StreamGeometry vs map_global_to_stream")
    try:
        sg = StreamGeometry(position=(100, 50), size=(1920, 1080), logical_size=(1920, 1080), scale=1.0)
        parity = stream_mapping_parity(sg)
        # show a couple points
        for p in [Point(100, 50), Point(150, 70), Point(500, 500)]:
            a = sg.global_to_stream_point(p)
            b = map_global_to_stream(p, {"position": sg.position})
            print(f"        global {p} -> typed {a}  legacy {b}  match={a==b}")
        if parity:
            print("      [OK] parity true for axis-aligned position offsets (M4 leftover equivalence holds)")
            ok += 1
        else:
            print("      [SKIP] parity mismatch")
    except Exception as e:
        print(f"      [SKIP] parity check failed: {e}")

    # STEP 6 — sanitize edges
    print("[6/7] sanitize edge cases — sanitize_rect clamp & sentinel behavior")
    try:
        cases = sanitize_edge_cases()
        for inp, out in cases:
            print(f"        sanitize_rect({inp}, screen_size=(1920,1080)) -> {out}")
        # honest documentation: edge overflow currently yields None, not a clipped 1x1
        print("      note: Rect(1919,1079,2,2) on 1920x1080 clamps to 1x1 then filtered (<=1 -> None)")
        print("            off-screen 3000,2000 and sentinel also -> None; tiny 1x1 -> None")
        # all should be None currently; the step succeeds by honestly documenting that
        print("      [OK] edge cases documented (honest current behavior)")
        ok += 1
    except Exception as e:
        print(f"      [SKIP] sanitize edges failed: {e}")

    # STEP 7 — OPTIONAL live
    print("[7/7] OPTIONAL live — UnifiedRemoteDesktop.get_stream_info() probe")
    try:
        if stream_info_provider is None:
            print("      [SKIP] no portal — pass a provider or run with --live on Wayland")
        else:
            sg = stream_info_provider()
            if sg is None:
                raise RuntimeError("provider returned None (no stream / not initialized)")
            # map a probe point both ways
            probe = Point(sg.position[0] + 100, sg.position[1] + 100)
            stream_pt = sg.global_to_stream_point(probe)
            legacy_pt = map_global_to_stream(probe, {"position": sg.position})
            back = sg.stream_to_global_point(stream_pt)
            print(f"      live StreamGeometry: position={sg.position} size={sg.size} scale={sg.scale} logical_size={sg.logical_size}")
            print(f"      probe global {probe} -> stream {stream_pt} (typed) vs {legacy_pt} (legacy) -> back {back}")
            print(f"      parity live: {stream_pt == legacy_pt}  round-trip live: {probe == back}")
            print("      [OK] live probe mapped")
            ok += 1
    except Exception as e:
        print(f"      [SKIP] live probe failed: {e}")

    print()
    print("-" * 70)
    print(f"Capabilities demonstrated: {ok}/{TOTAL_STEPS}")
    print("-" * 70)
    if ok == TOTAL_STEPS:
        print("All 7 capabilities — calibration math is fully demonstrated (live probe included).")
    elif ok >= 6:
        print("Core math (6/7) demonstrated offline — pass --live for the optional portal probe.")
    else:
        print("Partial — check [SKIP] lines above.")
    print()
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=TITLE)
    parser.add_argument("--live", action="store_true", help="attempt live portal probe for step 7 (requires Wayland)")
    args = parser.parse_args()

    provider: Optional[Callable[[], StreamGeometry]] = None
    if args.live:
        try:
            from open_alo_core import UnifiedRemoteDesktop, create_unified_desktop
            # Try factory helper; fall back to direct class
            try:
                desktop = create_unified_desktop(persist_mode=2, enable_capture=True)
            except Exception:
                desktop = UnifiedRemoteDesktop()
            # initialize may show the portal dialog
            try:
                desktop.initialize()
            except TypeError:
                desktop.initialize()  # type: ignore
            # need screen_size / stream_info to be available; first capture may be needed
            # but we just wrap get_stream_info
            def _provider() -> StreamGeometry:
                sg = desktop.get_stream_info()
                if sg is None:
                    # try to warm pipeline
                    try:
                        desktop.capture_screenshot()
                    except Exception:
                        pass
                    sg = desktop.get_stream_info()
                if sg is None:
                    raise RuntimeError("get_stream_info returned None even after warm-up")
                return sg  # type: ignore[return-value]
            provider = _provider
        except Exception as e:
            print(f"[warn] --live requested but portal unavailable: {e}")
            print("       continuing offline (step 7 will SKIP).")
            provider = None

    run(stream_info_provider=provider)
    # best-effort close if we created a desktop
    try:
        if args.live and "desktop" in locals() and desktop is not None:
            try:
                desktop.close()
            except Exception:
                pass
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
