# 04 — Calibration Workbench — the math layer that makes clicks land

> **Mostly pure; one optional live step.** GTK4 lies. At 2× the AT-SPI
> accessibility tree reports logical pixels while Mutter composites physical
> pixels. Without an affine correction every click lands half a window off.

This showcase isolates the *calibration* layer — pure geometry in
`AffineTransform2D` / `solve_affine` / `residual` plus the thin portal
helpers `StreamGeometry` and `sanitize_rect`. Six steps run headless; a
seventh proves the live mapping only if you pass `--live`.

---

## Why calibration exists

```
┌──────────────┐   AT-SPI bounding box      ┌────────────────┐
│  GTK4 app    │ ── Rect(0,0,927,524) ───►  │  Mutter global │
│ (logical)    │   1854×1048 physical       │  Rect(66,50,   │
└──────────────┘                           │   1854,1048)   │
                                           └────────────────┘
         need:  x_global = scale_x * x_local + offset_x
```

For every matched window Rect the solver infers the affine that maps
AT-SPI space → Mutter space:

```
scale_x  = mutter.width  / atspi.width
scale_y  = mutter.height / atspi.height
offset_x = mutter.x - scale_x * atspi.x
offset_y = mutter.y - scale_y * atspi.y
```

For the canonical GTK4 case `atspi=Rect(0,0,927,524)`,
`mutter=Rect(66,50,1854,1048)` the scales are exactly `2.0` and the
residual (`Chebyshev max |dx,dy,dw,dh|` between `transform_rect(atspi)` and
`mutter`) is `0.0 px`. `RuntimeCalibrator` accepts the fit only when
`residual < RESIDUAL_LIMIT_PX = 2.0 px` — otherwise it demotes grounding to
`VISION_ONLY`.

### Math derivation block

Given one matched rect pair the system is over-determined (4 equations,
4 unknowns) but consistent for axis-aligned scaling:

```
Let  tr = AffineTransform2D(sx, sy, ox, oy)
     tr.transform_rect(atspi)
       = Rect( round(sx*atspi.x + ox),
               round(sy*atspi.y + oy),
               max(1, round(sx*atspi.width)),
               max(1, round(sy*atspi.height)) )

Set tr.transform_rect(atspi) == mutter (integer rounding aside) and solve:

  sx = mutter.width  / atspi.width          (≈2.0 for GTK4 2×)
  sy = mutter.height / atspi.height         (≈2.0)
  ox = mutter.x - sx * atspi.x              (66 when atspi.x=0)
  oy = mutter.y - sy * atspi.y              (50 when atspi.y=0)

Residual (calibration.py:30-42):
  residual(mutter, atspi, t) = max( |tr.x-mutter.x|,
                                    |tr.y-mutter.y|,
                                    |tr.width-mutter.width|,
                                    |tr.height-mutter.height| )  # Chebyshev
  passes iff residual < 2.0
```

Integer rounding in `transform_point` / `inverse_point` means a 0–1 px
round-trip error is unavoidable and expected (`geometry.py:23-28, 37-44`).

---

## What you will see

Running `example.py` prints a banner, enumerates the seven capabilities,
then executes numbered steps (`[OK]` or `[SKIP]`) with a final
`Capabilities demonstrated: N/7` footer.

| Step | What it shows | Result offline |
|------|--------------|----------------|
| 1 — `gtk4_case` | `solve_affine(mutter, atspi)` → `AffineTransform2D(2.0,2.0,66,50)` + `residual` | `[OK]` |
| 2 — round-trip | `transform_point` → `inverse_point` on 5 points; max error | `[OK] ≤1 px` |
| 3 — demote policy | `residual < RESIDUAL_LIMIT_PX` table; which case flips to `VISION_ONLY` | `[OK]` |
| 4 — fractional scale | `StreamGeometry(scale=1.25, logical_size=(1536,864), size=(1920,1080))` round-trip | `[OK]` |
| 5 — parity | `StreamGeometry.global_to_stream_point` vs legacy `map_global_to_stream` | `[OK]` |
| 6 — sanitize edges | `sanitize_rect` sentinel, 1×1, off-screen, `Rect(1919,1079,2,2)` | `[OK]` (documents `None`s honestly) |
| 7 — OPTIONAL live | calls `stream_info_provider()` (`UnifiedRemoteDesktop.get_stream_info()`) if given | `[SKIP no portal]` offline |

Step 7 becomes `[OK]` only with `--live` on Wayland or with an injected
`stream_info_provider`.

---

## Fractional-scale open item

> **Open item:** the calibrator's in-memory cache is keyed by
> `(node_id, window_rect)` but does **not yet include `scale_hint`**.
> On GNOME with `scale=1.25` a fractional-scale change that leaves
> `position`/`size` unchanged could therefore reuse a stale
> `AffineTransform2D` until the window moves. The showcase prints this
> explicitly in step 4 and `fractional_scale_note()["note"]`.

The worked example uses the same geometry the compositor advertises in
`StreamGeometry`:

```
logical_size=(1536,864)  * 1.25 → size=(1920,1080)
StreamGeometry.global_to_stream_point / stream_to_global_point round-trip: 0 px
```

---

## Run

```bash
# From the repo root — offline (steps 1-6 OK, 7 SKIP)
python OPEN_ALO/examples/04_calibration_workbench/example.py

# With live probe (needs Wayland + portal; will show the permission dialog once)
python OPEN_ALO/examples/04_calibration_workbench/example.py --live

# Headless tests (no Wayland / portal needed)
pytest OPEN_ALO/examples/04_calibration_workbench -q
# or verbose
pytest OPEN_ALO/examples/04_calibration_workbench/test_04_calibration_workbench.py -v
```

### Expected output (snippet, offline)

```
======================================================================
OPEN_ALO CAPABILITY SHOWCASE
======================================================================
04 — Calibration Workbench — the math layer that makes clicks land

This run demonstrates:
  1. GTK4 2x affine fit (solve_affine + residual + RESIDUAL_LIMIT_PX)
  2. Round-trip integer error (transform_point / inverse_point)
  ...

[1/7] gtk4_case — solve_affine(mutter, atspi) + residual
      atspi : Rect(0, 0, 927, 524)
      mutter: Rect(66, 50, 1854, 1048)
      AffineTransform2D(scale_x=2.000000, scale_y=2.000000, offset_x=66.0, offset_y=50.0)
      residual=0.0000 px  limit=2.0  passes=True
      [OK] scale ≈2.0 (GTK4 reports half physical pixels)
[2/7] roundtrip_error — transform ↔ inverse (int rounding)
      max error = 0 px (expected <=1 px due to int rounding)
      [OK] round-trip within 1 px
...
[4/7] fractional scale — StreamGeometry(scale=1.25) round-trip
      StreamGeometry(position=(0, 0), size=(1920, 1080), logical_size=(1536, 864), scale=1.25)
      ...
      NOTE: OPEN ITEM: calibrator cache key does not yet include scale_hint. ...
      [OK] fractional-scale walk-through complete
[5/7] stream mapping parity — StreamGeometry vs map_global_to_stream
      [OK] parity true for axis-aligned position offsets (M4 leftover equivalence holds)
[6/7] sanitize edge cases — sanitize_rect clamp & sentinel behavior
        sanitize_rect(Rect(-2147483648, -2147483648, 100, 100), screen_size=(1920,1080)) -> None
        sanitize_rect(Rect(10, 10, 1, 1), screen_size=(1920,1080)) -> None
        sanitize_rect(Rect(3000, 2000, 100, 100), screen_size=(1920,1080)) -> None
        sanitize_rect(Rect(1919, 1079, 2, 2), screen_size=(1920,1080)) -> None
      note: Rect(1919,1079,2,2) on 1920x1080 clamps to 1x1 then filtered (<=1 -> None)
      [OK] edge cases documented (honest current behavior)
[7/7] OPTIONAL live — UnifiedRemoteDesktop.get_stream_info() probe
      [SKIP no portal] pass a provider or run with --live on Wayland

----------------------------------------------------------------------
Capabilities demonstrated: 6/7
----------------------------------------------------------------------
Core math (6/7) demonstrated offline — pass --live for the optional portal probe.
```

Passing `--live` (or injecting `run(stream_info_provider=...)` in a test)
flips step 7 to `[OK]` and the footer to `7/7`.

---

## Capability → API map

Every row lists the exact file + line anchor so `grep -n` stays honest.

| # | Capability | API | File ref | Notes |
|---|------------|-----|----------|-------|
| 1 | 2-D affine type (frozen, defaults, rounded int mapping) | `AffineTransform2D(scale_x=1.0, scale_y=1.0, offset_x=0.0, offset_y=0.0)`<br>`transform_point` / `transform_rect` (`max(1, round(...))`)<br>`inverse_point` / `inverse_rect` (`ValueError` on zero scale) | `src/open_alo_core/geometry.py:9-53`<br>`transform_point:23-27`, `transform_rect:29-35`, `inverse_point:37-43`, `inverse_rect:45-53` | `geometry.py` — dataclass is frozen; `transform_rect` floor-clamps w/h to ≥1 |
| 2 | Solve affine from matched rect pair | `solve_affine(mutter_rect, atspi_rect) -> AffineTransform2D` | `src/open_alo_core/calibration.py:12-27` | `sx=w_m/w_a, sy=h_m/h_a, ox=x_m-sx*x_a, oy=y_m-sy*y_a`; raises `ValueError` on degenerate `atspi` (`w<=0 or h<=0`) |
| 3 | Chebyshev residual + limit | `residual(mutter, atspi, t) -> float` (`max |dx,dy,dw,dh|`); `RESIDUAL_LIMIT_PX = 2.0` | `src/open_alo_core/calibration.py:9`, `calibration.py:30-42` | `RuntimeCalibrator` rule: `ok = residual < 2.0` else `VISION_ONLY` |
| 4 | Stream geometry (fractional scale, viewport) | `StreamGeometry(position, size, logical_size, scale, node_id, source_type)`<br>`is_in_stream` / `clamp_to_stream` / `stream_to_global_point` / `global_to_stream_point` | `src/open_alo_core/types.py:65-148`<br>methods `92-103`, `105-118`, `120-122`, `124-126` | `StreamGeometry` is a frozen dataclass; `size` is physical pixels, `logical_size` is `round(size/scale)` |
| 5 | Legacy ↔ typed mapping parity | `utils.map_global_to_stream(point, {"position": pos})` vs `sg.global_to_stream_point(point)` | `src/open_alo_core/utils/__init__.py:180-204` + `types.py:124-126` | M4 leftover equivalence; both subtract `position` — documented in `stream_mapping_parity()` |
| 6 | Rect sanitization | `sanitize_rect(rect, screen_size) -> Optional[Rect]` | `src/open_alo_core/utils/__init__.py:127-177` | Filters `INT_MIN` sentinel, `w<=1 or h<=1`, fully off-screen, then clamps and re-checks `<=1`; `Rect(1919,1079,2,2)` on 1920×1080 → `None` (clamped 1×1 filtered) |
| 7 | Live stream info (optional) | `UnifiedRemoteDesktop.get_stream_info() -> Optional[StreamGeometry]` | `src/open_alo_core/wayland/unified.py:913` (and showcase `example.py:run(step 7)`) | Step 7 only; `--live` wraps `create_unified_desktop(persist_mode=2, enable_capture=True)` |

Helper contracts exposed by `example.py`:

* `gtk4_case() -> dict{sx,sy,ox,oy,residual,passes}` — the GTK4 2× identity case (`atspi 927×524` vs `mutter 1854×1048`).
* `roundtrip_error(t, sample_points) -> int` — max Chebyshev error after `transform`→`inverse` (≤1 px expected).
* `demote_policy_demo(cases) -> list[(name,residual,ok)]` — `ok = residual < RESIDUAL_LIMIT_PX` verbatim.
* `fractional_scale_note() -> dict{geometry,samples,max_roundtrip_error,note}` — worked 1.25× example with the open-item callout.
* `stream_mapping_parity(sg) -> bool` — typed vs legacy equivalence for a few points.
* `sanitize_edge_cases() -> list[(Rect, Optional[Rect])]` — honest current `None`/`Rect` behavior.
* `run(stream_info_provider=None) -> int` / `main(): --live` — seven `[OK]/[SKIP]` steps + `Capabilities demonstrated: N/7`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ValueError: Invalid AT-SPI extents` | `atspi_rect.width<=0 or height<=0` passed to `solve_affine` | Sanitise with `sanitize_rect` first; never calibrate on sentinel/tiny rects |
| `ValueError: Cannot invert affine transform with zero scale` | `AffineTransform2D(0, …).inverse_point()` | Don't construct zero scale; gate with `scale_x != 0` |
| `residual` >> 2 px on real desktop | Window moved between AT-SPI snapshot and Mutter rect, or fractional scale drift | Re-snapshot both rects lock-step; check step 3 — will demote to `VISION_ONLY` |
| `sanitize_rect(Rect(1919,1079,2,2))` → `None` surprises | Clamp to 1920×1080 leaves 1×1 → filter `<=1` | Expected; see step 6 note. Test for `None` explicitly |
| `map_global_to_stream` and `global_to_stream_point` disagree | `position` in dict vs `sg.position` diverged (e.g. multi-monitor offset bug) | Ensure `{"position": sg.position}` — parity helper proves they should match |
| Step 7 `[SKIP no portal]` even with `--live` | Not Wayland, portal not running, or permission denied | Check `is_portal_available()` / `$XDG_SESSION_TYPE == wayland` / approve the dialog |

---

## See also

* `src/open_alo_core/geometry.py` — `AffineTransform2D` (rounded, floor-clamped)
* `src/open_alo_core/calibration.py` — `solve_affine` / `residual` / `RESIDUAL_LIMIT_PX`
* `src/open_alo_core/types.py:65-148` — `StreamGeometry`
* `src/open_alo_core/utils/__init__.py:127-204` — `sanitize_rect` / `map_global_to_stream`
* `examples/00_environment_doctor` — session/portal liveness probes
* `examples/01_unified_session_capture` — flagship full portal session
