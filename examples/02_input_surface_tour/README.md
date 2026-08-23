# 02 — Input Surface Tour

**Every input injector, each guarded by geometric safety preflight. No agent loops; a guided tour.**

This example enumerates the complete `UnifiedRemoteDesktop` input surface. Every injection
is preceded by a `GeometricPreflight` safety gate (bounds + occlusion) — the same gate a
real agent must pass before touching the desktop.

> **Run inside your own scratch editor** (e.g. GNOME Text Editor with an empty document).
> The tour targets *whatever window has focus* and types `OPEN_ALO input tour` into it.
> Pass `--no-spawn` to explicitly confirm you do not want a new window spawned
> (the default is already no-spawn).

```bash
python example.py              # targets focused window
python example.py --no-spawn   # same — accepted for compatibility
pytest test_02_input_surface_tour.py -v      # headless, no portal required
```

---

## Sign Conventions

* **Vertical scroll**: `scroll(clicks, x?, y?)` — `clicks > 0` means **UP**, `clicks < 0` means **DOWN**.
  The underlying portal call is `NotifyPointerAxisDiscrete` with axis `0` (vertical). The wrapper
  passes `clicks` directly, so the sign is preserved end-to-end. `scroll(-2)` in the tour
  therefore scrolls *down* two wheel detents.

* **Horizontal scroll**: `hscroll(clicks, ...)` uses axis `1`. `clicks > 0` means **RIGHT**,
  `clicks < 0` means **LEFT**.

* **Smooth scroll**: `smooth_scroll(dx, dy, finish?)` sends `NotifyPointerAxis` (continuous).
  `dx` is horizontal, `dy` vertical — sign follows the same convention as discrete scroll.
  The tour calls `smooth_scroll(dx=0, dy=40)` then `smooth_scroll(finish=True)` to close the
  gesture.

## GTK4 80 ms Hold Note

`UnifiedRemoteDesktop.click(Point, button=1) -> int` (`wayland/unified.py:236`) does not emit
an instantaneous press/release pair. The implementation inserts:

```python
time.sleep(max(delay, 0.08))  # between pressed=True and pressed=False
```

where `delay = pause if pause>0 else 0.05`. GTK4 gesture recognizers treat a <10 ms hold as
noise — a press/release with <10 ms gap can select a sidebar row without activating it.
The 80 ms guarantee was measured live; the tour calls `click` via the normal path so you
observe the same timing. `double_click` (`:542`) is two `click` calls with `interval=0.1`.

## Why Preflight Gates Every Step

Wayland has no global coordinate safety net. A blind `click(Point(5000,500))` or a click
through a higher window would either be clamped unpredictably or drive the wrong
application. `GeometricPreflight` (`open_alo_core/preflight.py:24`) provides two pure,
zero-dependency checks that return `Verdict(is_safe, reason)`:

1. **`verify_point_bounds(pt, stream_size)`** — rejects sentinel values (`-2147483648`),
   negative coordinates, and points outside `stream_size` via `sanitize_rect(Rect(x,y,2,2))`.
   This catches the `Point(1919,1079)` edge on a 1920×1080 stream: `Rect(1919,1079,2,2)`
   clamps to `1×1` and is rejected as `width<=1`.

2. **`verify_point_occlusion(pt, win_id, window_rects, z_order)`** — walks `z_order`
   above `win_id` and rejects the point if it lies inside any higher window's `Rect`
   (inclusive-edge `contains`).

`plan_injections(points, window_rects, z_order, target_win_id, stream_size=(1920,1080))`
runs **both** checks per point via a single `GeometricPreflight()` instance. The tour
consults its result before *every* real injection; if `is_safe is False` it prints
`[SKIP reason]` and never calls the portal.

```
point ──► verify_point_bounds ──► fail ──► [SKIP bounds]
             │
             └─► pass ──► verify_point_occlusion ──► fail ──► [SKIP occluded]
                              │
                              └─► pass ──► injection
```

The Step 2 table demonstrates each outcome:

| Point | Window setup | Expected verdict |
|-------|--------------|------------------|
| screen/target center | target window only, no higher window | `is_safe=True` |
| `Point(1919,1079)` on 1920×1080 | any | `is_safe=False` bounds/sentinel |
| `Point` inside a higher window's `Rect` while `target_win_id` is lower | `z_order=[lower, higher]` | `is_safe=False` occluded |

## Capability → API Map

Line refs are against `src/open_alo_core/wayland/unified.py`.

| Capability (tour step) | API | Line | Notes |
|------------------------|-----|------|-------|
| Config: read/set throttle & modes | `desktop.pause` / `fail_safe` / `touch_mode` | `:1365` | `@property` trio; tour prints before values then sets `pause=0.03` |
| Move cursor (absolute) | `move_mouse(Point)` | `:276` | `NotifyPointerMotionAbsolute` |
| Primary click (timestamp) | `click(Point, button=1) -> int` | `:236` | `button` 1/2/3 → evdev `0x110/0x112/0x111`; GTK4 `max(delay,0.08)` hold; returns `timestamp_ns` |
| Double click | `double_click(Point, button=1, interval=0.1)` | `:542` | two `click` calls spaced by `interval` |
| Type text | `type_text(text, interval=0.01)` | `:295` | per-char `NotifyKeyboardKeysym` |
| Single key (normalized) | `press_key(key) -> int` | `:318` | `normalize_key(key)` (`open_alo_core/types.py`); `enter→Return, esc→Escape, ctrl→Control` |
| Shortcut (Shift-aware) | `key_combo(keys: List[str])` | `:349` | normalizes each key; **bare uppercase letters are lowercased when no Shift in combo** — `["ctrl","A"]==["ctrl","a"]`, `["ctrl","shift","s"]` preserves case |
| Press sequence | `press_keys(keys, interval=0.1)` | `:569` | sequential `press_key` |
| Vertical wheel | `scroll(clicks, x?, y?)` | `:389` | `axis=0` discrete; **positive=UP**; optional `x,y` moves cursor first |
| Horizontal wheel | `hscroll(clicks, x?, y?)` | `:423` | `axis=1`; positive=RIGHT |
| Smooth/touchpad scroll | `smooth_scroll(dx=0, dy=0, finish=False)` | `:443` | `NotifyPointerAxis` |
| Drag with interpolation | `drag(start, end, button=1, duration=0.0)` | `:461` | interpolated `steps=max(int(duration/0.05),5)` then `NotifyPointerMotionAbsolute`; tour uses `duration=0.3` across `target width*0.25` margins |
| Swipe (natural motion) | `swipe(start, end, duration=0.3, steps=10, button=1)` | `:494` | `steps` intermediate motions, `time.sleep(duration/steps)` each |
| Hold modifier | `hold_key(key)` | `:528` | `@contextmanager` press/yield/release; tour does `with hold_key("Shift"): click(...)` |
| Relative motion | `move_mouse_relative(dx, dy)` | `:552` | `NotifyPointerMotion` (relative); tour moves `+15,+15` then `-15,-15` |
| Safety gate (bounds) | `GeometricPreflight.verify_point_bounds(pt, stream_size)` | `preflight.py:24` | `-> Verdict(is_safe, reason)` via `sanitize_rect` |
| Safety gate (occlusion) | `GeometricPreflight.verify_point_occlusion(pt, win_id, window_rects, z_order)` | `preflight.py:24` | `-> Verdict`; `reason` contains `"occluded"` on failure |
| Key normalization | `normalize_key(key)` | `types.py` | lowercases then `KEY_ALIASES` map |
| Window map for preflight | `WindowManager.list_windows()` + `Rect(w.x,w.y,w.width,w.height)` ; `get_window_z_order() -> List[int]` | `window_manager.py` | tour builds `{w.id: Rect(...)}` and `z_order` bottom→top |
| Banner / steps / footer | conventions | — | Banner `OPEN_ALO CAPABILITY SHOWCASE`; numbered `[OK]/[SKIP]`; footer `Capabilities demonstrated: N/M` |

## Tour Step List (12 steps)

1. **Config** — print `pause/fail_safe/touch_mode` then set `pause=0.03`
2. **Preflight table** — `plan_injections` for center (safe), corner `1919,1079` (bounds), synthetic occluded point (occluded) + `key_combo_normalization_demo()` docs
3. `move_mouse` to safe point (`:276`)
4. `click` left + right + `double_click` (`:236/:542`)
5. `type_text("OPEN_ALO input tour")` (`:295`)
6. `press_key Return` + `key_combo ["ctrl","a"]` then `["ctrl","c"]` (`:318/:349`)
7. `scroll -2 / +2`, `hscroll`, `smooth_scroll` at current pointer (`:389/:423/:443`)
8. `drag` across target window `width*0.25` margins `duration=0.3` (`:461`)
9. `swipe` downward (`:494`)
10. `hold_key Shift` + click (`:528`)
11. `move_mouse_relative` (`:552`)
12. `press_keys ["o","p","e","n"]` (`:569`)

Every injection step consults `plan_injections` for its point and prints `[SKIP reason]` if unsafe.

## Headless Tests

```bash
pytest examples/02_input_surface_tour/test_02_input_surface_tour.py -v
```

* `test_key_combo_docs_shape` — pure doc helper shape
* `test_plan_injections_safe_center` — center of `Rect(0,0,1920,1080)` with `z_order [1]` → safe
* `test_plan_injections_occluded` — point inside higher window while target is lower → `is_safe False` reason contains `occluded`
* `test_plan_injections_bounds_edge` — `Point(5000,500)` → bounds failure
* `test_run_with_mocks` — `MagicMock` desktop+wm (`get_window_z_order->[1]`, `list_windows->[]`) runs without exception and asserts `desktop.click >=2` and `smooth_scroll ==1`

No portal, no Wayland, no display required.

## Further Reading

* `src/open_alo_core/wayland/unified.py` — input surface source
* `src/open_alo_core/preflight.py` — `GeometricPreflight`
* `src/open_alo_core/types.py` — `Point`, `Rect`, `normalize_key`
* `API_REFERENCE.md` — full API docs
