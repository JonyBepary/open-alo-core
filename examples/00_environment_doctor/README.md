# 00 — Environment Doctor — Can this machine drive OPEN_ALO?

Zero permissions required. Zero desktop side effects. Answers the single question every newcomer has: *will anything portal/hardware-related block me before I write real automation?*

## What you will see

Running `example.py` prints a banner, enumerates every capability it will probe, then executes six numbered steps. Each probe maps to a real portal/hardware dependency that later OPEN_ALO lanes will need:

| Step | What it probes | Why it matters later |
|------|---------------|----------------------|
| 1 — Session | Wayland vs X11, portal availability, PipeWire | No Wayland + portal + PipeWire → no input/capture |
| 2 — Clock | Monotonic nanoseconds | Timestamp correlation for capture/AT-SPI sync |
| 3 — Geometry | `Point`/`Size`/`Rect` center, `contains()` inclusive edge, overflow rect `Rect(1919,1079,2,2)` | Coordinate math underpins every click/assertion |
| 4 — Sanitization | `sanitize_rect` sentinel, tiny-rect filter, off-screen clamp, pass-through | AT-SPI bounding boxes are noisy; sanitization prevents mis-clicks |
| 5 — Keymap | `normalize_key` aliases | Key strings must match portal keysym expectations |
| 6 — Exceptions | Uninitialized `UnifiedRemoteDesktop().click` | Correct `CoreError`/`RuntimeError` taxonomy for robust error handling |

All probes run locally without showing any permission dialog, opening windows, or touching the filesystem beyond Python imports.

## Requirements

- Python 3.10+
- `OPEN_ALO/src` on `sys.path` (handled by `example.py` header)
- Optional system deps (only affect probe *results*, not ability to run):
  - `PyGObject` (`gi`) with `Gio`/`GLib` for portal detection
  - `pw-cli` on `$PATH` for PipeWire detection
  - Wayland session (`WAYLAND_DISPLAY` set) for full capability

Install core in editable mode if you want imports outside examples:

```bash
pip install -e OPEN_ALO/
# or just rely on the sys.path insert in example.py
```

## How to run

From the repository root:

```bash
python OPEN_ALO/examples/00_environment_doctor/example.py
```

Headless tests (no Wayland/portal needed):

```bash
pytest OPEN_ALO/examples/00_environment_doctor -q
# or
pytest examples/00_environment_doctor -q   # when cwd is OPEN_ALO/
```

## Expected output (snippet)

```
OPEN_ALO CAPABILITY SHOWCASE — ENVIRONMENT DOCTOR
=================================================

Can this machine drive OPEN_ALO? Zero permissions, zero side effects.

This run demonstrates:
  1. Session / portal / PipeWire probing (detect_session_type, is_wayland, is_portal_available, is_pipewire_available)
  2. Monotonic clock (get_monotonic_ns)
  3. Geometry primitives (Point / Size / Rect — center, contains inclusive edge, 1919,1079 edge case)
  4. Rect sanitization (sanitize_rect — INT_MIN sentinel, 1x1 filter, off-screen clamp, pass-through)
  5. Key normalization (normalize_key — enter/esc/ctrl/del/pageup/unknown)
  6. Exception taxonomy (UnifiedRemoteDesktop uninitialized → RuntimeError/InputError family)

STEP 1 — Session probes
  session_type=x11  is_wayland=False  portal=False  pipewire=False
  [OK] session probes executed
STEP 2 — Monotonic clock
  t1=1234567890123  t2=1234567890456  delta=333  monotonic=True
  [OK] clock is monotonic (positive delta)
STEP 3 — Geometry playground
  Rect(0,0,100,50).center == Point(50,25) -> Point(50, 25)
  Rect(0,0,100,50).contains(Point(100,25)) inclusive edge -> True
  Rect(0,0,100,50).contains(Point(100,50)) corner inclusive -> True
  Rect(1919,1079,2,2).center -> Point(1920, 1080)
  Rect(1919,1079,2,2).bottom_right -> Point(1921, 1081)
  Rect(1919,1079,2,2).contains(Point(1920,1080)) inclusive -> True
  Size(1920,1080) -> Size(1920, 1080)
  [OK] geometry primitives behave correctly
STEP 4 — Rect sanitization
  sanitize_rect(Rect(-2147483648, -2147483648, 100, 100)) -> None
  sanitize_rect(Rect(10, 10, 1, 1)) -> None
  sanitize_rect(Rect(1800, 900, 300, 300)) -> Rect(1800, 900, 120, 180)
  sanitize_rect(Rect(10, 20, 100, 50)) -> Rect(10, 20, 100, 50)
  sanitize_rect(Rect(10, 20, 100, 50)) -> Rect(10, 20, 100, 50)
  [OK] sanitize_rect covers sentinel, 1x1, clamp, pass-through
STEP 5 — Key normalization
  normalize_key('enter') -> 'Return'
  normalize_key('esc') -> 'Escape'
  normalize_key('ctrl') -> 'Control'
  normalize_key('del') -> 'Delete'
  normalize_key('pageup') -> 'Page_Up'
  normalize_key('unknown') -> 'unknown'
  [OK] all six key mappings correct
STEP 6 — Exception taxonomy
  UnifiedRemoteDesktop().click without init raised: RuntimeError
  [OK] caught and classified as RuntimeError

Capabilities demonstrated: 6/6
```

Values for `session_type`, `portal`, `pipewire`, and timestamps will differ per machine. All six `[OK]` lines should appear on any machine; a headless CI box without Wayland still gets `6/6` because the probes succeed at *reporting* the (negative) state.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `session_type=unknown  is_wayland=False  portal=False` | Running under X11, headless CI, or `WAYLAND_DISPLAY` not set | Expected outside a Wayland session. Lanes needing input/capture will need Wayland. |
| `portal=False` even on Wayland | `xdg-desktop-portal` not running, or `PyGObject` not installed | `sudo apt install xdg-desktop-portal python3-gi` then re-login |
| `pipewire=False` | `pipewire` not running or `pw-cli` missing | `sudo apt install pipewire` and ensure `pw-cli info` exits 0 |
| `t2 - t1 == 0` flagged as failure | Extremely fast successive calls (rare) | Re-run; `get_monotonic_ns` uses `GLib.get_monotonic_time` or `time.monotonic_ns()` fallback |
| Import error for `open_alo_core` | Running from wrong `cwd` without `src` on path | Use `python OPEN_ALO/examples/00_environment_doctor/example.py` from repo root, or `pip install -e OPEN_ALO/` |

## Capability → API map

| Capability | API | File ref |
|------------|-----|----------|
| Detect Wayland/X11 session | `detect_session_type()`, `is_wayland()` | `src/open_alo_core/utils/__init__.py` ~11–46 |
| Portal availability | `is_portal_available()` | `src/open_alo_core/utils/__init__.py` ~49–85 |
| PipeWire availability | `is_pipewire_available()` | `src/open_alo_core/utils/__init__.py` ~88–101 |
| Monotonic clock (ns) | `get_monotonic_ns()` | `src/open_alo_core/utils/__init__.py` ~104–124 |
| Global→stream coordinate mapping | `map_global_to_stream()` | `src/open_alo_core/utils/__init__.py` ~180–204 |
| Rect sanitization / clamping | `sanitize_rect(rect, screen_size)` | `src/open_alo_core/utils/__init__.py` ~127–177 |
| Geometry primitives | `Point`, `Size`, `Rect` (+ `center`, `contains()`, `top_left`, `bottom_right`) | `src/open_alo_core/types.py` |
| Stream geometry helpers | `StreamGeometry` | `src/open_alo_core/types.py` ~64–148 |
| Key normalization | `normalize_key(key)`, `KEY_ALIASES` | `src/open_alo_core/types.py` ~155–198 |
| Exception taxonomy | `CoreError`, `InputError`, `SessionError`, `CaptureError`, `PermissionDenied`, `BackendNotAvailable` | `src/open_alo_core/exceptions.py` |
| Input surface (used to verify taxonomy) | `UnifiedRemoteDesktop().click(Point)` | `src/open_alo_core/wayland/unified.py` ~236–274 |

> **Note on file refs:** `utils/__init__.py` line numbers drift with edits; ranges above are approximate (`~`). Use `grep -n` to locate symbols precisely.
