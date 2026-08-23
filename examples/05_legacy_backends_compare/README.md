# 05 — Legacy Backends Compare

> **The two single-purpose backends vs unified — and when each still wins.**

`WaylandCapture` (ScreenCast one-shot) and `WaylandInput` (RemoteDesktop input) each
require their **own** portal dialog and session. `UnifiedRemoteDesktop` collapses both
into **ONE** grant (RemoteDesktop + ScreenCast). This example renders the trade-offs
as an aligned comparison table, probes each legacy backend live (with safe defaults),
and tells you which backend to pick.

---

## What you will see

Running `example.py` on a Wayland desktop (GNOME/KDE + `xdg-desktop-portal`):

1. **Comparison table** — 5 aspects, each row mentions all three backends, rendered
   aligned with width ≤120. Columns: *Aspect*, *Legacy (WaylandCapture / WaylandInput)*,
   *UnifiedRemoteDesktop*.
2. **`capture_once()` live probe** — `WaylandCapture()` context manager →
   `capture_screen() -> CaptureResult(data, source_type, size)`; saves PNG to
   `/tmp/open_alo_05_legacy.png`; prints `source_type` + `size`; `[SKIP]` if portal
   denied (ephemeral `close()` after each capture).
3. **Input probe (opt-in)** — `WaylandInput().initialize(persist_mode=0)` →
   `key_combo(["ctrl","l"])` → `close()`. **Skipped by default** — you must pass
   `--with-input` to inject keys (typing into the user's session unprompted is rude).
4. **Guidance** — `agents → UnifiedRemoteDesktop` plus the two remaining niches for
   the legacy backends.

Second run of `UnifiedRemoteDesktop` with `persist_mode=2` reuses its token and skips
the dialog; the legacy backends have separate token files (see below).

Headless / X11 / no portal: steps 2–3 print `[SKIP]` and the footer shows
`Capabilities demonstrated: 2/4` (table + guidance) — nothing crashes.

---

## Decision matrix — when to use each

| Scenario | Pick | Why |
|----------|------|-----|
| **Kiosk screenshot** — one PNG, no input, throwaway | `WaylandCapture` | Ephemeral: `close()` after each `capture_screen()`; no token to manage; PNG one-shot via `pipewiresrc … ! pngenc ! appsink` |
| **Input-only automation** on a stable host | `WaylandInput` | Full input (click/move/type/press_key/key_combo); persistent `tokens.json`; no capture overhead |
| **Any agent / loop / lockstep observation** | `UnifiedRemoteDesktop` | **ONE** dialog for RemoteDesktop + ScreenCast; PNG **plus** raw-RGB streaming (`appsink`); persistent `unified_token.json`; lockstep `capture_observation()`; preflight/drag/scroll |
| Need raw-RGB + stride for CV | `UnifiedRemoteDesktop` | Legacy capture is PNG-only; unified has `capture_raw_rgb()` / `get_frame_rgb()` with stride padding |
| Need to avoid second dialog at all costs | `UnifiedRemoteDesktop` | Legacy needs 2 dialogs if you need both capture and input |

**Rule of thumb:** if you need *both* capture and input, always use `UnifiedRemoteDesktop`.
The legacy backends only win when you need *exactly one* capability and want the smallest
possible permission surface.

---

## Token persistence

| Backend | Token file | Written by | Read on | Persist modes |
|---------|------------|------------|---------|---------------|
| `WaylandInput` | `~/.config/open_alo_core/tokens.json` | `WaylandInput._save_token()` after `SelectDevices` → `Start` | next `initialize(persist_mode>0)` via `_load_token()` | `0`=never (dialog every time), `1`=while app running, `2`=until revoked |
| `UnifiedRemoteDesktop` | `~/.config/open_alo_core/unified_token.json` | `UnifiedRemoteDesktop._save_token()` after `SelectDevices` / `Start` | next `initialize(persist_mode=2)` via `_load_token()` | same `0/1/2`; `2` is recommended |

`WaylandCapture` is **ephemeral**: it calls `close()` after each `capture_screen()` and does
not persist a token (portal session per capture). Delete the token file(s) or revoke in
Settings → Privacy → Screen Sharing / Remote Desktop to force the dialog again.

Format of both token files:

```json
{"restore_token": "...", "timestamp": 171..., "version": 1}
```

---

## Run

```bash
# From the repo root — safe (no input injection)
python OPEN_ALO/examples/05_legacy_backends_compare/example.py

# Actually probe input (will send Ctrl+L)
python OPEN_ALO/examples/05_legacy_backends_compare/example.py --with-input

# Headless tests (no portal needed)
pytest OPEN_ALO/examples/05_legacy_backends_compare/test_05_legacy_backends_compare.py -v
```

---

## Capability → API map

All line refs are relative to `src/open_alo_core/wayland/`.

| # | Capability | API | File:line | Notes |
|---|------------|-----|-----------|-------|
| 1 | Comparison table (dialogs / capture / input / lifetime / recommended-for) | `comparison_table() -> List[Tuple[aspect, legacy, unified]]` (example helper) | `examples/05_legacy_backends_compare/example.py:34` | Each row mentions `WaylandCapture`, `WaylandInput`, `UnifiedRemoteDesktop` across cells; rendered via `_format_table()` ≤120 cols |
| 2 | One-shot PNG capture (ephemeral) | `WaylandCapture` context manager; `capture_screen() -> CaptureResult(data:bytes, source_type:str in {"monitor","window","camera"}, size:(w,h))` | `wayland/capture.py:39`, `wayland/capture.py:94-142` | Internally ` _create_session` → `_select_sources(types=MONITOR,cursor_mode=2)` → `_start_capture() -> (node_id,metadata)` → `_capture_frame` via `pipewiresrc path={node} num-buffers=1 ! videoconvert ! video/x-raw,format=RGB ! pngenc ! appsink` with 10s wall clock (`wayland/capture.py:236-277`); `close()` after each `capture_screen()` (ephemeral) |
| 3 | Input probe (opt-in) | `WaylandInput.initialize(persist_mode) -> bool` token file default `~/.config/open_alo_core/tokens.json`; `key_combo(keys)` Shift-aware lowercasing | `wayland/input.py:74`, `wayland/input.py:258`, `wayland/input.py:494` | `initialize(persist_mode=0)` demo; `click(Point,button)` (`wayland/input.py:154` delay `getattr(_pause,0.05)`), `move_mouse` (`wayland/input.py:183`), `type_text(text,interval=0.01)` (`wayland/input.py:203`), `press_key` (`wayland/input.py:230` `normalize_key`), `_notify_pointer_motion_absolute` primary `(oa{sv}udd)` fallback `(oa{sv}dd)` (`wayland/input.py:414-443`), `_notify_keyboard_keysym` `NotifyKeyboardKeysym` (`wayland/input.py:476`) |
| 4 | Guidance (agents → unified) | `UnifiedRemoteDesktop` (recommended for agents) | `wayland/unified.py:47`, token `wayland/unified.py:99-110` | Single dialog, `unified_token.json`, PNG+raw-RGB streaming, lockstep observation |

Helper contracts in `example.py`:

* `comparison_table() -> list[(aspect, legacy, unified)]` — 5 rows: dialogs required (1 per backend vs 1 total), capture (PNG one-shot vs PNG+raw-RGB streaming), input (none for Capture / full for Input), session lifetime (ephemeral vs persistent + restore_token), recommended-for (kiosk screenshot / input-only automation / agents).
* `capture_once() -> Optional[(bytes,int)]` — `with WaylandCapture() as cap: cap.capture_screen()` → `(data, len(data))` or `None` on exception.
* `input_probe(keys=["ctrl","l"]) -> bool` — `WaylandInput().initialize(persist_mode=0)` then `key_combo(keys)`, `close()`; exceptions → `False`.
* `run(skip_live=False, with_input=False)` — 4 steps `[1/4]…[4/4]` with `[OK]`/`[SKIP]`, footer `Capabilities demonstrated: N/4` (table counts as 1), `agents → UnifiedRemoteDesktop` guidance.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `CaptureError: Screen capture failed` / `[SKIP] portal denied` on step 2 | Denied ScreenCast dialog, or not on Wayland, or PipeWire not running | Re-run and click **Allow** on the portal's source picker; check `echo $XDG_SESSION_TYPE` == `wayland`, `systemctl --user status xdg-desktop-portal pipewire` |
| Step 3 always `[SKIP]` | Default is skip (rude to type unprompted) | Pass `--with-input` to actually probe `WaylandInput` |
| `input_probe` returns `False` even with `--with-input` | `WaylandInput.initialize` returns `False` / portal denied, or not on Wayland | Approve the RemoteDesktop dialog; check `~/.config/open_alo_core/tokens.json` writable; try `persist_mode=2` manually |
| Dialog appears every run | `persist_mode=0` (this example's input probe) or token file missing | For real automation use `persist_mode=2`; verify token file exists after first approval |
| `ImportError: No module named 'gi'` | PyGObject not installed | `sudo apt install python3-gi python3-gi-cairo gstreamer1.0-pipewire` |
| `GStreamer error` / `Failed to capture frame within timeout` | No PipeWire node, or `num-buffers=1` pipeline starved | Ensure monitor source selected (`types=MONITOR`); check `pipewiresrc` plugin installed (`gst-inspect-1.0 pipewiresrc`) |

---

## See also

* `01_unified_session_capture` — flagship ONE-dialog unified session (recommended for agents)
* `API_REFERENCE.md` — full `WaylandCapture` / `WaylandInput` / `UnifiedRemoteDesktop` reference
* `architecture/UNIFIED_REMOTEDESKTOP_APPROACH.md` — portal flow (CreateSession → SelectDevices/SelectSources → Start)
