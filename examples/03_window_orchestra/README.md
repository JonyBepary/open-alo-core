# 03 — Window Orchestra — the complete WindowManager surface, live and state-restoring

> **Live demo of every `WindowManager` capability — with guaranteed state restoration.**

This example exercises the entire `WindowManager` API in one run: utility-window filtering, search, z-order, focus, geometry, fullscreen, minimize, details and workspace moves. Every mutation is wrapped in `try/except` (prints `[SKIP reason]` on failure) and every change is undone before the next step, so your desktop is left exactly as it was found.

---

## Extension requirement

All window operations require the **window-actions** GNOME Shell extension (v1.17, `window-actions@openalo.local`) that exposes D-Bus at `org.gnome.Shell.Extensions.Windows`.

Install from the repository root:

```bash
make -C window-actions-alo install
# — or manually —
# mkdir -p ~/.local/share/gnome-shell/extensions/window-actions@openalo.local
# cp window-actions-alo/extension.js window-actions-alo/metadata.json ~/.local/share/gnome-shell/extensions/window-actions@openalo.local/
```

Then restart GNOME Shell (logout/login or <kbd>Alt</kbd>+<kbd>F2</kbd> → `r` on X11) and enable the extension:

```bash
gnome-extensions enable window-actions@openalo.local
```

Verify:

```bash
gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/Windows --method org.gnome.Shell.Extensions.Windows.List
```

If the call returns `('[]',)` or a JSON array the extension is live. If it returns an error, `WindowManager()` will raise `RuntimeError` and every step in this example will print `[SKIP]` gracefully.

---

## State-restoration promise

| Mutation | Restoration |
|---|---|
| `activate(editor.id)` | No persistent state — focus naturally returns when demo exits |
| `move_resize(100,100,900,600)` | Before-rect captured via `get_frame_rect`; no auto-restore (visual only) but next steps restore sizing |
| `maximize` | `unmaximize` immediately after (`[5]`) |
| `make_fullscreen` | `toggle_fullscreen` (off) + `unmake_fullscreen` if still fullscreen (`[5]`) |
| `minimize` | `unminimize` immediately after (`[6]`) |
| `move_to_workspace(1)` | `move_to_workspace(original_workspace)` immediately after (`[8]`) |
| `close(editor.id)` | Only if the demo spawned the editor (`spawn_editor()` returned a `Popen`); pre-existing windows are never closed |
| Spawned `Popen` | `terminate()` → `wait(2)` → `kill()` fallback (`[9]`) |

Leak check: `list_windows()` count before vs after is printed in step 9. Any spawned window is closed and its process terminated before the demo returns.

---

## Run

```bash
# From the repo root
python OPEN_ALO/examples/03_window_orchestra/example.py

# Headless tests (no GNOME / D-Bus needed)
pytest OPEN_ALO/examples/03_window_orchestra/test_03_window_orchestra.py -v
```

---

## What you will see (live)

```
======================================================================
OPEN_ALO CAPABILITY SHOWCASE
======================================================================
03 — Window Orchestra  |  the complete WindowManager surface, live and state-restoring

[1/9] inventory — list_windows() vs include_utility=True + classify
      clean count (include_utility=False): 3
      all count   (include_utility=True):  4
      kept=3 hidden=1 (via utility_diff)
        [HIDDEN (utility)] id=... wm_class='gjs' title='Desktop Icons ...'
        [kept] id=... wm_class='org.gnome.TextEditor' ...
      [OK] inventory complete
[2/9] focused window — get_focused_window() + get_details()
      focused: id=... wm_class='firefox' title='Mozilla Firefox'
      [OK] focused window inspected
[3/9] spawn editor — spawn_editor() + wait_for_window('TextEditor', timeout=8)
      spawned pid=12345
      [OK] editor window: id=... title='Text Editor' workspace=0
[4/9] z-order — get_window_z_order() before/after activate(editor.id)
      z-order before: [...] (len=3)
      z-order after : [...] (len=3)
      editor index 1 -> 2 (top is len-1=2)
      [OK] z-order snapshot + activate
[5/9] geometry dance — get_frame_rect -> move_resize -> maximize -> unmaximize -> fullscreen toggle
      rect before: {'x': 0, 'y': 0, 'width': 800, 'height': 600}
      move_resize(100,100,900,600) -> True
      rect after move_resize: {'x': 100, 'y': 100, 'width': 900, 'height': 600}
      verified change: {...} -> {...}
      maximize -> True
      unmaximize (restore) -> True
      make_fullscreen -> True
      toggle_fullscreen (off) -> True
      [OK] geometry dance complete (state restored)
[6/9] minimize+unminimize with 0.4s sleeps
      minimize -> True
      unminimize (restore) -> True
      [OK] minimize cycle (restored)
[7/9] get_details — maximized/canclose flags
      details: maximized=0 canclose=True fullscreen=False
      [OK] get_details flags inspected
[8/9] move_to_workspace(1) then back to original workspace
      original workspace: 0
      move_to_workspace(1) -> True
      move_to_workspace(0) restore -> True
      [OK] workspace move restored
[9/9] cleanup — close(editor.id)+terminate popen, leak check
      close(...) -> True
      popen terminated
      leak check: initial=3 before_cleanup=4 after=3
      [OK] no leak detected
      [OK] cleanup complete

----------------------------------------------------------------------
Capabilities demonstrated: 9/9
----------------------------------------------------------------------
All 9 capabilities live — WindowManager is fully operational and state was restored.
```

Headless / extension missing: every step prints `[SKIP] reason` and the footer shows `Capabilities demonstrated: 0/9` (or partial) — nothing crashes.

---

## Capability → API map

All symbols are in `src/open_alo_core/window_manager.py` unless noted. `WindowInfo` fields: `id, wm_class, title, x, y, width, height, workspace, focus, maximized` (plus `wm_class_instance, pid, monitor, frame_type, window_type, in_current_workspace`).

| # | Capability | API | Line | Notes |
|---|------------|-----|------|-------|
| — | Filter flag | `WindowManager(timeout=5, include_utility=False)` | `window_manager.py:101` | Default hides utility windows; `True` keeps gjs Desktop Icons + null wm_class |
| — | Utility heuristic | `is_utility_window(win) -> bool` (top-level fn `69-78` + `WindowManager._is_utility_window` staticmethod alias `99`) | `window_manager.py:69-78, 99` | `not wm_class` → True; `gjs` + `Desktop Icons` prefix → True |
| 1 | List windows (filtered) | `list_windows(current_workspace_only=False) -> List[WindowInfo]` | `window_manager.py:212, 261` | Filtered when `include_utility is False`; probes `List` D-Bus method |
| 1 | Helpers built on list | `classify_windows(windows) -> list[(WindowInfo\|dict, bool)]` + `utility_diff(all_windows) -> (kept, hidden)` | `example.py` | Teaches **why** default list is clean: maps `is_utility_window` and splits |
| 2 | Focused window | `get_focused_window() -> Optional[WindowInfo]` | `window_manager.py:408` | Scans `list_windows()` for `focus==True` |
| 2,7 | Window details | `get_details(id) -> Optional[dict]` | `window_manager.py:421` | D-Bus `Details`; keys include `maximized, canclose, fullscreen` |
| — | Title by id | `get_title(id) -> Optional[str]` | `window_manager.py:436` | D-Bus `GetTitle` with dual-quote JSON unwrapping |
| 3 | Spawn helper | `spawn_editor() -> Optional[Popen]` | `example.py` | `subprocess.Popen(["gnome-text-editor","--new-window"])`; `FileNotFoundError → None` |
| 3 | Poll for window | `wait_for_window(query, match_title=True, timeout=5, poll_interval=0.05)` | `window_manager.py:375` | Polls `find_window` until found or timeout |
| 1,3 | Find (single) | `find_window(query, match_title=True) -> Optional[WindowInfo]` | `window_manager.py:266` | Bidirectional fuzzy: `query in wm_class` **or** `wm_class in query`; then title |
| — | Find (all) | `find_all_windows(query, match_title=True) -> List[WindowInfo]` | `window_manager.py:303` | Same fuzzy logic, returns all matches |
| 4 | Z-order (utility-scrubbed) | `get_window_z_order() -> List[int]` | `window_manager.py:333-373` | D-Bus `GetWindowZOrder` + second `List` call to scrub utility ids; fallback to `list_windows()` order |
| 4 | Activation | `activate(id) -> bool` | `window_manager.py:485` | D-Bus `Activate`; verified via z-order index move |
| 5 | Frame rect | `get_frame_rect(id) -> Optional[Dict]` | `window_manager.py:631` | D-Bus `GetFrameRect`; alias `get_frame_bounds` (`646`) |
| 5 | Move / resize | `move(id,x,y)`, `resize(id,w,h)`, `move_resize(id,x,y,w,h)` | `window_manager.py:582, 597, 612` | D-Bus `Move`/`Resize`/`MoveResize` |
| 5 | Maximize cycle | `maximize(id)` / `unmaximize(id)` | `window_manager.py:498, 503` | D-Bus `Maximize`/`Unmaximize` |
| 5 | Fullscreen cycle | `make_fullscreen(id)`, `unmake_fullscreen(id)`, `toggle_fullscreen(id)` | `window_manager.py:523, 540, 557` | `toggle` checks `get_details(...).fullscreen` then delegates |
| 6 | Minimize cycle | `minimize(id)` / `unminimize(id)` | `window_manager.py:508, 513` | D-Bus `Minimize`/`Unminimize` with 0.4 s sleeps |
| 7 | Detail flags | `get_details(id)` → `maximized / canclose` | `window_manager.py:421` | Printed in step 7 |
| 8 | Workspace move | `move_to_workspace(id, ws) -> bool` | `window_manager.py:663` | D-Bus `MoveToWorkspace`; demo moves to `1` then back to original `editor.workspace` |
| 9 | Close + leak check | `close(id) -> bool` + `list_windows()` count | `window_manager.py:518` | Only for spawned windows; `Popen.terminate()` + `kill()` fallback |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `WindowManager init failed: Window Calls extension not available` | Extension not installed or not enabled | `make -C window-actions install` then `gnome-extensions enable window-actions@openalo.local` + re-login |
| `list_windows()` returns `[]` | D-Bus `List` returned empty or extension not responding | Verify `gdbus call ... Windows.List` returns JSON; restart GNOME Shell |
| `get_window_z_order()` fallback | `GetWindowZOrder` not in extension build | Update extension to v1.17; fallback uses `list_windows()` order |
| `spawn_editor returned None` | `gnome-text-editor` not installed | `sudo apt install gnome-text-editor` (or `gedit`); step 3 will `[SKIP]` gracefully and remaining editor steps skip |
| `wait_for_window timed out` | Editor launched but not yet mapped (Wayland compositor delay) | Increase `timeout` to `8`; check `wm.find_window("TextEditor")` manually |
| `move_resize` has no visible effect | Wayland compositor ignores positioning for some clients / tiling | Try `move` + `resize` separately; check `get_frame_rect` delta |
| `move_to_workspace` no effect | Only one workspace exists | Create a second workspace in GNOME Settings → Multitasking |
| Import error for `open_alo_core` | Running from wrong `cwd` without `src` on path | Use `python OPEN_ALO/examples/03_window_orchestra/example.py` from repo root, or `pip install -e OPEN_ALO/` |

---

## See also

* `src/open_alo_core/window_manager.py` — full implementation
* `window-actions/extension.js` — GNOME Shell extension source (D-Bus surface `window-actions@openalo.local`)
* `OPEN_ALO/examples/00_environment_doctor` — zero-permission probes
* `OPEN_ALO/examples/01_unified_session_capture` — unified portal session flagship
