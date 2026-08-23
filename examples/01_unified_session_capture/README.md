# 01 — Unified Session Capture

> **Flagship intro — one permission dialog → full input + capture session.**

This example is the recommended entry point for `open_alo_core`. A single
`UnifiedRemoteDesktop` portal grant gives you mouse/keyboard injection **and**
PipeWire screen capture for the lifetime of the approval — no second dialog,
no split controllers.

---

## What you will see

When you run `example.py` on a Wayland desktop (GNOME/KDE with
`xdg-desktop-portal`):

1. **ONE system permission dialog** appears — title *“Allow Remote Desktop / ScreenCast”*
   with device (keyboard/mouse) and source (monitor) checkboxes. Approve once.
2. The terminal prints a numbered showcase (`OPEN_ALO CAPABILITY SHOWCASE`,
   steps `[1/8] … [8/8]`) with `[OK]` or `[SKIP]` per step and a final
   `Capabilities demonstrated: N/8` footer.
3. Step 4 writes `/tmp/open_alo_01_screenshot.png` (blocking `pull-sample`,
   ~500 ms on first frame while PipeWire negotiates).
4. Step 5 prints 5 paced `get_frame()` sizes ~200 ms apart — proves the
   `pipewiresrc → appsink` pipeline is flowing (`max-buffers=1 drop=true`).
5. Step 6 prints a monotonic `timestamp_ns` from `capture_observation()` and
   asserts `png` is non-empty.
6. Step 7 prints raw RGB shape `(h, w, 3)` and notes GStreamer row padding
   (`stride` may exceed `w*3`).

**Second run skips the dialog.** With `persist_mode=2` (default) the portal
issues a `restore_token` saved to `~/.config/open_alo_core/unified_token.json`.
The next `initialize()` reuses it silently — remove that file to force the
dialog again.

Headless / X11 / no portal: every step prints `[SKIP] reason` and the footer
shows `Capabilities demonstrated: 0/8` (or partial) — nothing crashes.

---

## Token persistence

| Location | `~/.config/open_alo_core/unified_token.json` |
|---|---|
| Written by | `UnifiedRemoteDesktop._save_token()` after `SelectDevices` / `Start` |
| Read on | next `initialize(persist_mode=2)` via `_load_token()` |
| Format | `{"restore_token": "...", "timestamp": 171..., "version": 1}` |
| Persist modes | `0` = never (dialog every time), `1` = while app running, `2` = until revoked (recommended) |
| Revoke | delete the file, or revoke in system Settings → Privacy → Screen Sharing |

---

## Run

```bash
# From the repo root
python OPEN_ALO/examples/01_unified_session_capture/example.py

# Headless tests (no portal needed)
pytest OPEN_ALO/examples/01_unified_session_capture/test_01_unified_session_capture.py -v
```

---

## Capability → API map

All methods belong to `UnifiedRemoteDesktop` in
`src/open_alo_core/wayland/unified.py` unless noted. Factory is at
`unified.py:1396`.

| # | Capability | API | Line | Notes |
|---|------------|-----|------|-------|
| 1 | Create & initialize single-permission session | `create_unified_desktop(persist_mode=2, enable_capture=True)` → `UnifiedRemoteDesktop` + `initialize() -> bool` | `unified.py:1396`, `unified.py:170` | One portal dialog for RemoteDesktop + ScreenCast. `persist_mode=2` enables restore token. |
| 2 | Screen resolution | `get_screen_size() -> Optional[Tuple[int,int]]` | `unified.py:989` | Reads caps from `appsink` pad; `None` until pipeline is PLAYING. |
| 3 | Stream metadata (typed + compat) | `get_stream_info() -> Optional[StreamGeometry]` | `unified.py:913` | **Typed since Aug 23.** Fields: `position`, `size=(1920,1080)`, `logical_size`, `scale`, `node_id`, `source_type`. Dict-compat via `info["scale"]` / `info.get("node_id")`. `logical_size = round(size/scale)` fallback. |
| 4 | Blocking screenshot | `capture_screenshot() -> bytes` | `unified.py:579` | `appsink.emit("pull-sample")` — blocks ~500 ms on first frame. Returns PNG bytes. |
| 5 | Non-blocking live frame | `get_frame() -> Optional[bytes]` | `unified.py:631` | `try-pull-sample` with 1 ms timeout; `None` if no frame ready. Ideal for tight agent loops. |
| 6 | Lockstep observation | `capture_observation() -> dict{png, timestamp_ns, stream_info: StreamGeometry, screen_size}` | `unified.py:677` | PNG + `GLib.get_monotonic_time()*1000` sampled immediately after buffer map; `stream_info` is a `StreamGeometry` instance. |
| 7 | Raw RGB + stride | `_ensure_raw_pipeline()` + `capture_raw_rgb() -> dict{buffer,width,height,stride,timestamp_ns,stream_info}` | `unified.py:748`, `unified.py:778` | `pipewiresrc → videoconvert → video/x-raw,format=RGB → appsink`. `stride` is bytes-per-row (GStreamer pads to 4-byte, often 64-byte). `get_frame_rgb()` (`unified.py:852`) is the non-blocking variant (1 ms). Buffer math: `buf[:stride*h].reshape(h,stride)[:,:w*3].reshape(h,w,3)` |
| 8 | Teardown | `close()` | `unified.py:203` | Sets both pipelines to `Gst.State.NULL`, then `portal.Close(session_handle)`. Safe to call multiple times. |

Helper contracts demonstrated in `example.py`:

* `describe_stream(geom) -> list[(field,value)]` mixes `geom.scale` / `geom.logical_size` (typed) with `geom["position"]` / `geom.get("node_id")` (legacy) to prove backward compatibility via `StreamGeometry.__getitem__` / `__get__` (`types.py:139-147`).
* `raw_to_image_shape(buf,width,stride) -> (h,w,3)` computes `h = len(buf)//stride` and returns `(h,w,3)` without requiring `numpy`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `PermissionDenied: User denied permission` | Denied the portal dialog, or portal not running | Re-run and click **Allow**. Check `is_portal_available()` / `systemctl --user status xdg-desktop-portal` |
| `PermissionDenied: User denied device/source access` | `SelectDevices` or `SelectSources` denied | Same — approve the dialog; ensure `persist_mode=2` and token file is writable |
| `SessionError: Failed to create session (code: …)` | Portal timeout or compositor denied | Ensure Wayland session (`echo $XDG_SESSION_TYPE` == `wayland`), GNOME/KDE running |
| `CaptureError: No PipeWire node available` / `No sample available` | `enable_capture=False` or PipeWire not running | Initialize with `enable_capture=True`; check `is_pipewire_available()` / `systemctl --user status pipewire` |
| `CaptureError: No sample available` on first frame | Pipeline still negotiating (~500 ms) | Retry or use blocking `capture_screenshot()` which waits; ensure monitor source selected |
| `get_stream_info() is None` | Called before `initialize()` or capture disabled | Call `initialize(enable_capture=True)` first |
| `get_screen_size() is None` | Pipeline not yet PLAYING | Call after `initialize()`; `_ensure_pipeline()` is lazy — first capture triggers it |
| Raw `stride != width*3` | Expected — GStreamer pads rows to 4-byte (sometimes 64-byte) boundary | Use `raw_to_image_shape()` math; logical pixels are `width*3` per row, physical row is `stride` |
| Dialog appears every run | `persist_mode=0` or token file missing/unreadable | Use `persist_mode=2`; verify `~/.config/open_alo_core/unified_token.json` exists after first approval |
| `ImportError: No module named 'gi'` | PyGObject not installed | `sudo apt install python3-gi python3-gi-cairo gstreamer1.0-pipewire` |

---

## See also

* `API_REFERENCE.md` — full `UnifiedRemoteDesktop` reference
* `docs/UNIFIED_QUICK_REFERENCE.md` — one-page cheat sheet
* `architecture/UNIFIED_REMOTEDESKTOP_APPROACH.md` — portal flow (CreateSession → SelectDevices/SelectSources → Start)
