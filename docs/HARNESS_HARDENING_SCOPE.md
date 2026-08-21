# Harness-Grade Hardening Scope — open_alo + window-actions → Data Collection Harness

**Branch:** `agent-a1d2728c64a4a507` · **Date:** 2026-05-13 · **Mode:** build (implementation)
**Upstream plan:** `Desktop Automation Agent: End-to-End Project Plan` (tooling substitution table, Phases 0-7)

This doc is the *pre-harness* hardening scope. It answers:
1. What to fix/extend in **open_alo** and **window-actions** *before* building the harness — so the harness is thin, reliable, and model-friendly.
2. What the **data dumps + live AT-SPI probe** on this real Ubuntu Wayland session teach us about policy, and how the harness must adapt.

---

## 1. What the data dumps + live probe actually say

### 1.1 Dumps audited

- `ui_tree.txt` — GNOME Terminal, `show_desktop_ui_tree_advanced.py --max-depth 12 --max-nodes 800` (X11 session, Feb 2026)
- `browser_tree.txt` — Brave (Chromium) on **XWayland**, same tool, 320 lines, 108 buttons, 2× `document web`, full toolbar/tab strip
- Live AT-SPI probe today (Wayland, 2026-05-13) via `pyatspi` on same machine: `WAYLAND_DISPLAY=wayland-0`, `XDG_SESSION_TYPE=wayland`, `gnome-shell` + `pipewire` + `xdg-desktop-portal` all live, 17 desktop children

### 1.2 Quantified recall (usable = has non-empty name *or* has real bbox `(w>1,h>1,x!=-2147483648)` and `VISIBLE`)

| Source | Buttons total | Usable bbox | Unnamed buttons | Notes |
|---|---|---|---|---|
| **ui_tree.txt (Terminal)** | 17 | 8 (47%) | 0 | Remaining 9 are `(-2147483648,1,1)` offscreen sentinels (hidden menus, zoom controls) |
| **browser_tree.txt (Brave/XWayland)** | 108 | 63 (58%) | 7 | 45 buttons at `(0,0,0,0)` or `(1,1)` — collapsed tab strip items, hidden extension buttons |
| **Live: Nautilus** | — | 19/20 actionable usable (95%) | — | Native GTK4 — excellent |
| **Live: Papers (PDF viewer)** | — | 6/7 (86%) | — | Native GTK — good |
| **Live: Terminal** | 75 actionable rows | 4 with has_bbox (frames only) | — | **71/75 menu items are `1×1` offscreen** — menus only get real extents when open |
| **Live: Brave/Wayland** | 3 nodes total | 2 | — | **Collapsed from 300+ to 3.** Chromium disables renderer a11y on Wayland unless `--force-renderer-accessibility`. Same binary, different compositor, opposite recall. |

**Read:** Native GTK apps → 85-95% recall, usable. Chromium/Electron on Wayland → catastrophic collapse to ~2% (frame shell only). XWayland masks the gap (58% in dump). The dump was collected on X11 where the problem was invisible.

### 1.3 Policy implications for the harness & model

1. **Vision-primary, a11y-accelerant.** Do not design the model to *require* a11y IDs. On your target suite, Brave (browser task) will almost certainly be in the low-recall regime in any West… (Wayland) deployment or customer machine. Treat OCR/visual element detection as the primary grounding path; use a11y IDs as *hints* when they exist (Nautilus/Papers). The plan's line "don't assume the hybrid wins" should become a hard rule: **fallback is vision→a11y, not a11y→vision.**
2. **Offscreen sentinel is the norm, not the exception.** `(-2147483648, -2147483648, 1, 1)` and `(0,0,0,0)` mean "not laid out / not showing." The harness must filter them at collection time and the model must never be trained to click them. Our `ui_tree.txt`/`browser_tree.txt` both contain them in bulk; training on raw trees without filtering would teach the model to hallucinate invisible targets.
3. **Menus are stateful.** Terminal's 71 menu items exist in the tree but are 1×1 until the menu is open. A static snapshot is insufficient; the harness must capture *pre-action → action (open menu) → post-action* as a trajectory, not a single frame. Synthetic generation should explicitly open menus before labeling click targets.
4. **Brave needs an a11y flag or it is vision-only.** For any Chromium-based target task, launch with `--force-renderer-accessibility` *and* set `ACCESSIBILITY_ENABLED=1` in the harness, or accept that web content will be `document web → section → (no children)` as in browser_tree's noVNC frame. Document this in the harness launcher; don't try to fix it in open_alo.
5. **Dump is X11-biased.** Browser_tree's 58% usable inflates true Wayland recall. Future dumps must be collected on the *same* `injected-input path` and same Wayland session the model will run on (Phase 1a rule). Re-collect on Wayland with the flag above and compare.

---

## 2. Improved open_alo scope (harness-facing, still zero-ML)

> Goal: keep `open_alo_core` lean and Wayland-correct, but make it *harness-ready* — timestamp lockstep, stream metadata you can normalize with, and failure modes you can train on. No tree sparsification, no VLM, no policy — those live in the harness.

### 2.1 Keep (already solid — 257 tests, 93% cov)

- `UnifiedRemoteDesktop` as the single entry point (`RemoteDesktop`+`ScreenCast` one permission). Legacy `WaylandInput`/`WaylandCapture` stay for compat but are not harness-facing.
- Absolute motion fix (`NotifyPointerMotionAbsolute` with stream `udd`, pixel logical coords), portal race fix (subscribe-before-call), hang-free `try-pull-sample`, fail-closed injection (no silent relative fallback), fail-fast `WindowManager`.
- Capture paths (`capture_screenshot` blocking PNG, `get_frame` non-blocking, `get_screen_size`).

### 2.2 Add before harness — small, high-leverage

#### A. Stream metadata exposure (P0 — 1 day)

**Why:** Harness must normalize coords to `[0,1]` for training but inject *pixels via absolute motion*. Absolute motion coords are in **stream logical space** (portal spec `NotifyPointerMotionAbsolute` docs). Today `open_alo` hides the stream: `_pipewire_node` is private, `size` is not exposed, `position`/`scale` never surfaced. Without it, `Point(800,600)` is ambiguous on multi-monitor HiDPI.

**Scope:**
- Expose `get_stream_info() -> {node_id, position=(x,y), size=(w,h), logical_size?, scale, is_primary}` by parsing `Start`'s `streams` `a{sv}` properly (today we only grab `node_id` from `streams[0][0]`; extend to capture `position`, `size`, `source_type`).
- Add `_stream_size`/`_stream_position` fields populated in `_start_session`; expose via public getters.
- New helper `normalize_point(Point) -> (nx,ny)` and `denormalize_point(nx,ny) -> Point` using stream logical size; harness calls these at clean time, not open_alo.
- Document the `logical_size` vs `size` portal doc mismatch (issue #1976) — if `logical_size` present use it, else fall back to `size`.

**Acceptance:** `tests/test_unified_mock.py` asserts `get_stream_info()["size"] == (1854,1048)` on mocked Start response; `normalize_point(Point(927,524)) == (0.5,0.5)` round-trips.

#### B. Timestamp-locked capture (P0 — 1 day)

**Why:** Plan Phase 1a requires `{timestamp, frame, full a11y tree, window state}` in lockstep. Today `capture_screenshot` and a11y/WM queries are separate calls with no shared clock. Dagger and offline eval need to know "what did the model see *when* it decided."

**Scope:**
- Add `capture_observation() -> {png: bytes, timestamp_ns: int (CLOCK_MONOTONIC), stream_info, monitor_geometry}` — single call that ensures pipeline, pulls sample, and samples `GLib.get_monotonic_time()` immediately after `buffer.map` success. No a11y inside open_alo (keep zero-ML), but timestamp lets the harness correlate its out-of-band AT-SPI snapshot (taken within ±50ms) as the same step.
- Keep `capture_screenshot`/`get_frame` for simple callers; `capture_observation` is the harness path.
- Add `get_monotonic_ns()` utility for harness to timestamp its own AT-SPI pass on the same clock.

**Acceptance:** Mock pipeline test asserts `obs["timestamp_ns"]` within 100ms of `get_monotonic_ns()` and `obs["png"]` non-empty.

#### C. Injection hardness for harness loops (P0 — 0.5 day)

Already fixed fail-closed; now add:
- `click()` / `press_key()` return the `timestamp_ns` of the injection (monotonic after `call_sync` success) so harness can log action time for later diffing.
- Document `enable_capture=False → absolute motion requires a stream` — if harness runs input-only, it must either enable capture or use `move_mouse_relative` explicitly. No silent fallback remains (we fixed that).

#### D. Capture robustness (P1 — 0.5 day)

- Handle PipeWire stream size *changes* mid-session (scale change): `_ensure_pipeline` should re-query `get_screen_size`/`get_stream_info` on failure and rebuild pipeline if size mismatch, not just reuse. Add a `reconfigure_on_size_change` flag for harness.
- Expose `cursor_mode` choice (embedded vs hidden vs metadata) as `initialize(cursor_mode=2)` param — harness may want cursor hidden for training (clean frames) or embedded for demo overlay visibility (Phase 7).

#### E. What NOT to add to open_alo

- No a11y tree building, no patch extraction, no sparsification, no OCR, no model, no allowlist — those are harness/policy layers (keeps `open_alo_core` `PyGObject`-only, installable anywhere). Provide a `harness/` package *next to* open_alo that imports it.

### 2.3 Tests & version

- New unit tests for A-C (6-8 tests) using existing mock portal/pipeline infra — no live Wayland needed.
- Bump to `0.2.1` or `0.3.0` after A-C land; keep `CHANGELOG.md` harness-facing (stream meta, timestamp API) separate from earlier portal fixes.

---

## 3. Improved window-actions scope (what the harness actually needs)

> We built a full window *actions* API (Move/Resize/Maximize/Minimize/Activate/Close + 8 query methods + 4 signals). The harness only needs a *window *state* API* plus one mutation.

### 3.1 What harness v1 actually needs (narrow)

| Need | Method | Why |
|---|---|---|
| Snapshot | `List()` + `Details(winid)` + `GetFrameRect(winid)` | Per-step window state for the `{a11y tree, window state}` log; focus/workspace/monitor for per-task success checks |
| Target selection | `GetFocusedWindow()` + `find_window(query)` (via python helper) | "Which app is this step acting in?" |
| Calibrate | `GetMonitorGeometry(i)` | Stream size ↔ monitor mapping for normalization |
| Single mutation | `MoveResize(winid,x,y,w,h)` | Synthetic generation (place windows deterministically) + reset between episodes |
| Lifecycle signals (optional) | `WindowCreated/Closed/FocusChanged` | Nice for live agent, but harness can just poll `List` each step — *not required for data collection* |

**Keep for now, but not harness-critical:** `Maximize`/`Unmaximize`/`Minimize`/`Move`/`Resize`/`Activate`/`Close` — we hardened them and they are tested (Maximize verified `width > 640`, Activate verified focus). Useful for demos and for DAgger intervention (close a stray dialog), but not needed to collect the first synthetic dataset. Don't extend further before harness proves need.

### 3.2 Small fixes before harness (P1 — 0.5 day total)

- **Expose `GetWorkspaceCount` / keep `position` in stream info** so harness can do `MoveToWorkspace` deterministically without guessing workspace indices (avoids `ListOnWorkspace(-1)` false-fail we flagged).
- **Document the a11y gap for browser tasks** in `docs/API.md`: "Brave/Chromium on Wayland: launch with `--force-renderer-accessibility` or treat web content as vision-only. See harness launcher env."
- **No new signals.** WorkspaceChanged is now present (introspection test); don't add per-window watches until the live agent needs them (Phase 6).

### 3.3 Tests

- Existing 44 checks already cover fail-closed Maximize/Unmaximize/Activate verifications and `WindowCreated`/`Closed`/WorkspaceChanged presence. Keep them; harness will add a synthetic `MoveResize→Details` round-trip as its own harness-level integration test, not as an extension unit test.

---

## 4. Recall-measurement harness (Week 1 gate)

> "Walk every element your target tasks need to click or type into and check whether AT-SPI reports a usable role, name, and bounding box." — measure now; don't assume hybrid wins.

### 4.1 Spec (`tools/recall_probe.py` — to be added)

- **Input:** task manifest `tasks.json` listing 5-10 tasks × target app + manual element list per task (e.g., Nautilus: sidebar item "Documents", toolbar "View Options", file grid item; Brave: address bar `entry` "Address and search bar", etc.)
- **Per element:** query AT-SPI by BFS for `role` + `name` + `extents` + `state (VISIBLE/SHOWING/ENABLED)`. Classify: `usable = name non-empty and bbox real and VISIBLE and (role expected)`.
- **Output:** per-app recall table like §1.2 but *task-sliced* — e.g., `Nautilus file-rename task: 4/5 elements usable (80%); blocked: context menu item "Rename" bbox=1×1 until menu open`.
- **Gate rule:** if any task's recall < 70%, that task is tagged `vision-primary` and the harness must generate a vision-grounded trajectory (OCR bbox + screenshot patch) alongside the a11y-ID trajectory. Don't average across apps — gate per task per app.

**Status:** Live probe above already does the core BFS; needs to be wrapped with a `tasks.json` and CSV/JSON report. Implement in next build turn (~2 hours).

### 4.2 What to do with results

- <70% tasks → prioritize patch extraction + OCR in harness Phase 1b over tree-ID labeling; keep tree as auxiliary feature, not primary action target.
- Menu/offscreen gaps → harness synthetic generation must *open* the menu first (stateful), not label a 1×1 sentinel as a target.

---

## 5. Portal-in-VM smoke test (Week 1 gate)

> "Prove that portal + Wayland + PipeWire actually produces frames and accepts input *inside* your disposable environment before building on it."

**This machine is already the positive control:** `XDG_SESSION_TYPE=wayland`, `WAYLAND_DISPLAY=wayland-0`, `pipewire` + `xdg-desktop-portal` live, `org.freedesktop.portal.Desktop` `NameHasOwner=true`, `window-actions` `List` returns real windows (tested). So the host path works. The risk is the *harness's disposable environment* — typically a container or nested compositor — which must replicate the same plumbing.

### 5.1 Smoke harness (`tools/portal_smoke.py` — to be added)

Three modes, same assertions:

| Mode | How to run | What it proves |
|---|---|---|
| **A. Host (this machine)** | `python tools/portal_smoke.py --mode host` | Cheap sanity: one `UnifiedRemoteDesktop.initialize(persist_mode=1)` in a temp session + `get_screen_size` + one `move_mouse_relative(1,0)` + `close`. No permission dialog if token cached; else shows it once. |
| **B. Nested Weston (recommended for CI)** | `weston --backend=headless --socket=wayland-test --xwayland &` + `pipewire` + `xdg-desktop-portal-wlr` or `xdg-desktop-portal-gnome` (headless backend) + `tools/portal_smoke.py --mode nested --wayland-display wayland-test` | Proves PipeWire frames can be produced headless without claiming the user's real desktop. This is the Phase 6 infra validated early. |
| **C. Container (podman/docker)** | Bind-mount `XDG_RUNTIME_DIR` + `WAYLAND_DISPLAY` + DBus session bus into container, run same smoke | Proves D-Bus/XDG_RUNTIME plumbing is correct. Often fails on `XDG_RUNTIME_DIR` perms or `at-spi-bus-launcher` not forwarded. |

**Pass criteria (fail-closed, like window-actions 44-check):**
- `get_screen_size()` returns `(w>0,h>0)`
- `capture_observation()` returns `png` with PNG magic `89 50 4E 47` and timestamp within 5s of now
- Injected motion returns no `InputError`
- `window-actions` `List` (if extension present) returns array (may be empty in nested Weston — that's OK)

**Why Weston not Xvfb:** Xvfb is X11-only, no compositor, no `org.freedesktop.portal.*`, no PipeWire screen cast. It will *always* fail `is_portal_available()` — don't use it. Weston headless + `pipewire` + portal impl is the minimal viable Wayland harness.

**Status:** Modes A and the helper are ready to land (~2 hours); Mode B/C require Weston/portal packages in the harness image — to be validated in the next turn by actually spawning headless Weston on this host if available, else documented as Week 1 task.

---

## 6. Build order (adjusted — one starting point)

1. **This scope (P0/P1 above) — 2-3 days:** land stream meta + timestamps in open_alo, freeze window-actions as-is, land `recall_probe` + `portal_smoke` tools.
2. **Phase 0 scoping + 1a harness prove-out:** pick 5 tasks (Nautilus file-ops, Papers annotation, Brave nav, Terminal command) and run `recall_probe` on each → decides vision-primary vs hybrid per task.
3. **1b synthetic for 2-3 high-recall tasks (Nautilus/Papers):** cheapest data, validates harness + `capture_observation` timestamp lockstep.
4. **Phase 4 pipeline skeleton + overfit on that tiny set:** action encode/decode round-trip test, closed-loop eval hook from day one.
5. Scale: more tasks, teleop where recall low (Brave), ablations, DAgger.

---

## 7. Open questions for you

- Target task list for v1: which 5-10 tasks? (proposed: Nautilus create/rename/move file, Papers highlight, Brave address-bar nav, Terminal run command + verify output file)
- Do you want AT-SPI *inside* `capture_observation` (heavier, but guarantees lockstep) or keep it harness-side with monotonic timestamps as spec'd above? Recommend harness-side to keep open_alo zero-ML, but can be debated.
- Persist mode for harness: `persist_mode=1` (per-run) in disposable env vs `2` on dev host — which token path do you want per environment?

