# OPEN_ALO Examples — Capability Showcase

Six intentional, self-contained showcases. **Run one and you immediately see what
`open_alo_core` can do** — every script prints a capability manifest up front,
executes numbered steps with `[OK]/[SKIP]`, and ends with a
`Capabilities demonstrated: N/M` scorecard.

## The Showcase Tour (run in order)

| Folder | What you will see | Permissions | Headless test |
|---|---|---|---|
| [`00_environment_doctor`](00_environment_doctor/) | Session/Wayland/portal/PipeWire probes, geometry + sanitize playground, keymap, exception taxonomy — **zero desktop side effects** | none | 22 tests |
| [`01_unified_session_capture`](01_unified_session_capture/) | One dialog → full session: typed `StreamGeometry`, screenshot, paced live frames, lockstep observation, stride-aware raw RGB | portal (input+capture) | 4 tests |
| [`02_input_surface_tour`](02_input_surface_tour/) | Every injector (click/type/key_combo/scroll/drag/swipe/hold_key…), each gated by `GeometricPreflight` bounds + occlusion checks | portal | 5 tests |
| [`03_window_orchestra`](03_window_orchestra/) | Full WindowManager surface incl. utility filtering, z-order, spawn+wait, geometry dance, fullscreen toggle — **state restored, no leaks** | extension only | 4 tests |
| [`04_calibration_workbench`](04_calibration_workbench/) | The math that makes clicks land: GTK4 2× affine solve, Chebyshev residual gating, inverse round-trips, fractional-scale walkthrough | none (`--live` adds portal) | 10 tests |
| [`05_legacy_backends_compare`](05_legacy_backends_compare/) | Decision matrix: `WaylandCapture` / `WaylandInput` vs unified; standalone PNG capture demo | portal (capture) | 4 tests |

```bash
# run any showcase
python3 examples/00_environment_doctor/example.py

# run its headless tests (no Wayland needed)
pytest examples/00_environment_doctor/
```

## Coverage Matrix — core export → showcase

| Core surface | API | Folder |
|---|---|---|
| Session probes | `detect_session_type`, `is_wayland`, `is_portal_available`, `is_pipewire_available`, `get_monotonic_ns` | 00 |
| Geometry primitives | `Point`, `Size`, `Rect.contains/center` | 00 |
| Rect hygiene | `sanitize_rect` (sentinel/garbage/clamp) | 00, 04 |
| Key normalisation | `normalize_key`, `KEY_ALIASES` | 00, 02 |
| Exception taxonomy | `PermissionDenied/CaptureError/InputError/SessionError` | 00 |
| Unified session | `create_unified_desktop`, `initialize(persist_mode=2)` + token persistence | 01 |
| Typed stream info | `get_stream_info() -> StreamGeometry` (+ dict-compat) | 01, 04 |
| Stream math | `StreamGeometry.is_in_stream/clamp_to_stream/stream↔global` | 04 |
| Capture (PNG) | `capture_screenshot`, `get_frame` | 01 |
| Capture (lockstep) | `capture_observation` (png + `timestamp_ns`) | 01 |
| Capture (raw RGB) | `capture_raw_rgb` / stride-aware buffer math | 01 |
| Input surface | `move/click/double_click/type_text/press_key/key_combo/press_keys` | 02 |
| Scroll family | `scroll/hscroll/smooth_scroll` | 02 |
| Drag family | `drag/swipe`, `hold_key`, `move_mouse_relative` | 02 |
| Safe injection | `GeometricPreflight.verify_point_bounds/verify_point_occlusion` | 02 |
| Window inventory | `list_windows(include_utility)`, `is_utility_window`, workspace filter | 03 |
| Window search | `find_window/find_all_windows/wait_for_window/get_focused/get_details/get_title` | 03 |
| Window state | `activate/maximize/unmaximize/minimize/unminimize/close/make_fullscreen/toggle_fullscreen` | 03 |
| Window geometry | `move/move_resize/get_frame_rect/get_frame_bounds` | 03 |
| Z-order & workspaces | `get_window_z_order`, `move_to_workspace` | 03 |
| Calibration math | `AffineTransform2D`, `solve_affine`, `residual`, `RESIDUAL_LIMIT_PX` | 04 |
| Legacy capture | `WaylandCapture.capture_screen` (ephemeral portal session) | 05 |
| Legacy input | `WaylandInput.initialize/click/key_combo` + token file | 05 |

## Requirements

* GNOME on Wayland + `xdg-desktop-portal-gnome`
* GStreamer ≥1.22 with PipeWire plugin (`pipewiresrc`)
* This repo's GNOME Shell extension: `make -C ../window-actions install` (folder 03)
* Python deps: `PyGObject`, `gstreamer` bindings; tests additionally use `pytest`

Folders `00` and `04` run fully offline — start there if you just want to see the
deterministic math layer work.
