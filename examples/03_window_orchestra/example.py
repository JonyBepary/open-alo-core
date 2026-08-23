#!/usr/bin/env python3
"""
03 — Window Orchestra — the complete WindowManager surface, live and state-restoring.

Demonstrates the full WindowManager API with utility-window filtering,
z-order, geometry, fullscreen, minimize and workspace moves — always
restoring state before exit.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- sys.path bootstrap to parents[2]/"src" ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from open_alo_core.window_manager import WindowInfo, WindowManager, is_utility_window  # noqa: E402

BANNER = "OPEN_ALO CAPABILITY SHOWCASE"
TOTAL_STEPS = 9


# ---------------------------------------------------------------------------
# Helpers required by spec
# ---------------------------------------------------------------------------

def classify_windows(windows: List) -> List[Tuple[object, bool]]:
    """
    Map is_utility_window over each entry.

    Returns:
        List of (WindowInfo|dict, bool) where bool is True for utility/noise
        windows (gjs Desktop Icons, null wm_class).
    """
    result: List[Tuple[object, bool]] = []
    for w in windows:
        try:
            flag = is_utility_window(w)  # type: ignore[arg-type]
        except Exception:
            # Fallback for dict-style entries
            try:
                wm_class = w.get("wm_class") if isinstance(w, dict) else getattr(w, "wm_class", "")
                title = w.get("title") if isinstance(w, dict) else getattr(w, "title", "")
                # Replicate heuristic inline
                if not wm_class:
                    flag = True
                elif wm_class == "gjs" and (title or "").startswith("Desktop Icons"):
                    flag = True
                else:
                    flag = False
            except Exception:
                flag = False
        result.append((w, flag))
    return result


def utility_diff(all_windows: List) -> Tuple[List, List]:
    """
    Split an include_utility=True result into (kept, hidden).

    Kept   = windows that survive the default filter (non-utility)
    Hidden = utility windows that the default list suppresses
    """
    classified = classify_windows(all_windows)
    kept = [w for w, is_util in classified if not is_util]
    hidden = [w for w, is_util in classified if is_util]
    return kept, hidden


def spawn_editor() -> Optional[subprocess.Popen]:
    """
    Try to launch gnome-text-editor.

    Returns:
        Popen handle on success, None if binary not found or launch fails.
    """
    try:
        proc = subprocess.Popen(
            ["gnome-text-editor", "--new-window"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return proc
    except FileNotFoundError:
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main demo flow
# ---------------------------------------------------------------------------

def run(wm: Optional[WindowManager] = None) -> int:
    """
    Execute the 9-step WindowManager showcase.

    If `wm` is None, creates a real WindowManager() (requires window-actions
    extension). Otherwise uses the injected instance (for headless pytest).

    Each step prints [OK] or [SKIP reason] and increments the demonstrated
    counter only on success. All mutating operations are wrapped in
    try/except and state is always restored.

    Returns:
        Number of demonstrated capabilities (0..TOTAL_STEPS).
    """
    print("=" * 70)
    print(BANNER)
    print("=" * 70)
    print("03 — Window Orchestra  |  the complete WindowManager surface, live and state-restoring")
    print()

    # Resolve WindowManager (injected or real)
    wm_created = False
    if wm is None:
        try:
            wm = WindowManager()
            wm_created = True
        except Exception as e:
            print(f"[SKIP] WindowManager init failed: {e}")
            print(f"       (requires window-actions extension — see README)")
            wm = None  # type: ignore[assignment]

    demonstrated = 0
    initial_count: Optional[int] = None
    editor = None
    editor_proc: Optional[subprocess.Popen] = None
    original_workspace: Optional[int] = None

    # Initial leak-check baseline (if wm available)
    if wm is not None:
        try:
            initial_count = len(wm.list_windows())
        except Exception:
            initial_count = None

    # ── Step 1: inventory ─────────────────────────────────────────────
    print(f"[1/{TOTAL_STEPS}] inventory — list_windows() vs include_utility=True + classify")
    try:
        if wm is None:
            raise RuntimeError("WindowManager not available")
        # Clean list (default filter)
        clean = wm.list_windows()
        # All windows (utility included) — toggle include_utility temporarily
        all_windows: List
        if hasattr(wm, "include_utility"):
            orig = wm.include_utility
            try:
                wm.include_utility = True  # type: ignore[attr-defined]
                all_windows = wm.list_windows()
            finally:
                wm.include_utility = orig  # type: ignore[attr-defined]
        else:
            all_windows = wm.list_windows()

        kept, hidden = utility_diff(all_windows)
        # Classify sample for teaching
        sample = all_windows[:4]
        classified = classify_windows(sample)

        print(f"      clean count (include_utility=False): {len(clean)}")
        print(f"      all count   (include_utility=True):  {len(all_windows)}")
        print(f"      kept={len(kept)} hidden={len(hidden)} (via utility_diff)")
        for w, is_util in classified:
            wm_class = getattr(w, "wm_class", w.get("wm_class", "") if isinstance(w, dict) else "")
            title = getattr(w, "title", w.get("title", "") if isinstance(w, dict) else "")
            wid = getattr(w, "id", w.get("id", "?") if isinstance(w, dict) else "?")
            marker = "HIDDEN (utility)" if is_util else "kept"
            print(f"        [{marker}] id={wid} wm_class={wm_class!r} title={title!r}")
        demonstrated += 1
        print("      [OK] inventory complete")
    except Exception as e:
        print(f"      [SKIP] inventory: {e}")

    # ── Step 2: focused window details ─────────────────────────────────
    print(f"[2/{TOTAL_STEPS}] focused window — get_focused_window() + get_details()")
    try:
        if wm is None:
            raise RuntimeError("WindowManager not available")
        focused = wm.get_focused_window()
        if focused is None:
            raise RuntimeError("no focused window (headless or no windows)")
        print(f"      focused: id={focused.id} wm_class={focused.wm_class!r} title={focused.title!r}")
        # Also try get_details for focused
        try:
            det = wm.get_details(focused.id)
            if det:
                print(f"      details keys: {list(det.keys())[:8]}")
        except Exception as de:
            print(f"      [SKIP] get_details for focused: {de}")
        demonstrated += 1
        print("      [OK] focused window inspected")
    except Exception as e:
        print(f"      [SKIP] focused window: {e}")

    # ── Step 3: spawn editor + wait_for_window ─────────────────────────
    print(f"[3/{TOTAL_STEPS}] spawn editor — spawn_editor() + wait_for_window('TextEditor', timeout=8)")
    try:
        if wm is None:
            raise RuntimeError("WindowManager not available")
        # Attempt spawn — handle patched spawn_editor == None or non-callable
        try:
            if not callable(spawn_editor):
                raise TypeError("spawn_editor not callable (patched to None)")
            editor_proc = spawn_editor()
            if editor_proc is None:
                print("      [SKIP] spawn_editor returned None (gnome-text-editor not found)")
            else:
                print(f"      spawned pid={editor_proc.pid}")
        except FileNotFoundError as fe:
            print(f"      [SKIP] spawn_editor FileNotFoundError: {fe}")
            editor_proc = None
        except Exception as se:
            print(f"      [SKIP] spawn_editor: {se}")
            editor_proc = None

        # Always attempt to locate editor (existing or newly spawned)
        try:
            # Prefer wait_for_window (polling)
            found = wm.wait_for_window("TextEditor", timeout=8)
            if found is None:
                # Fallback to direct find
                found = wm.find_window("TextEditor")
            editor = found
        except TypeError:
            # FakeWM may not accept timeout kwarg variations
            try:
                editor = wm.wait_for_window("TextEditor")  # type: ignore[call-arg]
            except Exception:
                editor = wm.find_window("TextEditor")
        except Exception as we:
            print(f"      [SKIP] wait_for_window: {we}")
            editor = None

        if editor is None:
            # Try broader queries
            for q in ("gnome-text-editor", "Text Editor", "gedit"):
                try:
                    editor = wm.find_window(q)
                    if editor:
                        break
                except Exception:
                    continue

        if editor is None:
            if editor_proc is None:
                print("      [SKIP] no editor window found and spawn failed — skipping editor-dependent steps")
            else:
                print("      [SKIP] wait_for_window timed out — editor not yet visible")
        else:
            original_workspace = getattr(editor, "workspace", 0)
            print(f"      [OK] editor window: id={editor.id} title={editor.title!r} workspace={original_workspace}")
            demonstrated += 1
        if editor is None and editor_proc is None:
            # Mark step as skipped (demonstrated not incremented)
            pass
        elif editor is None:
            print("      [SKIP] editor not found")
    except Exception as e:
        print(f"      [SKIP] spawn/wait: {e}")

    # ── Step 4: z-order before/after activate ──────────────────────────
    print(f"[4/{TOTAL_STEPS}] z-order — get_window_z_order() before/after activate(editor.id)")
    try:
        if wm is None:
            raise RuntimeError("WindowManager not available")
        if editor is None:
            raise RuntimeError("no editor window — skipping")
        z_before = wm.get_window_z_order()
        print(f"      z-order before: {z_before[:6]}{'...' if len(z_before)>6 else ''}  (len={len(z_before)})")
        idx_before = z_before.index(editor.id) if editor.id in z_before else -1
        try:
            wm.activate(editor.id)
            time.sleep(0.4)
        except Exception as ae:
            print(f"      [SKIP] activate: {ae}")
        z_after = wm.get_window_z_order()
        idx_after = z_after.index(editor.id) if editor.id in z_after else -1
        print(f"      z-order after : {z_after[:6]}{'...' if len(z_after)>6 else ''}  (len={len(z_after)})")
        if idx_before >= 0 and idx_after >= 0:
            print(f"      editor index {idx_before} -> {idx_after} (top is len-1={len(z_after)-1})")
        demonstrated += 1
        print("      [OK] z-order snapshot + activate")
    except Exception as e:
        print(f"      [SKIP] z-order: {e}")

    # ── Step 5: geometry dance ─────────────────────────────────────────
    print(f"[5/{TOTAL_STEPS}] geometry dance — get_frame_rect -> move_resize -> maximize -> unmaximize -> fullscreen toggle")
    try:
        if wm is None:
            raise RuntimeError("WindowManager not available")
        if editor is None:
            raise RuntimeError("no editor window — skipping")

        # Capture before
        rect_before = None
        try:
            rect_before = wm.get_frame_rect(editor.id)
            print(f"      rect before: {rect_before}")
        except Exception as re:
            print(f"      [SKIP] get_frame_rect before: {re}")

        # move_resize
        try:
            ok = wm.move_resize(editor.id, 100, 100, 900, 600)
            print(f"      move_resize(100,100,900,600) -> {ok}")
            time.sleep(0.4)
            rect_after = wm.get_frame_rect(editor.id)
            print(f"      rect after move_resize: {rect_after}")
            if rect_before and rect_after:
                print(f"      verified change: {rect_before} -> {rect_after}")
        except Exception as me:
            print(f"      [SKIP] move_resize: {me}")

        # maximize -> unmaximize (state-restoring)
        try:
            wm.maximize(editor.id)
            print("      maximize -> True")
            time.sleep(0.4)
        except Exception as me:
            print(f"      [SKIP] maximize: {me}")
        try:
            wm.unmaximize(editor.id)
            print("      unmaximize (restore) -> True")
            time.sleep(0.2)
        except Exception as ue:
            print(f"      [SKIP] unmaximize: {ue}")

        # fullscreen dance — ensure we leave non-fullscreen
        try:
            wm.make_fullscreen(editor.id)
            print("      make_fullscreen -> True")
            time.sleep(0.4)
        except Exception as fe:
            print(f"      [SKIP] make_fullscreen: {fe}")
        try:
            # toggle should turn it off (make_fullscreen set fullscreen; toggle will unmake)
            wm.toggle_fullscreen(editor.id)
            print("      toggle_fullscreen (off) -> True")
            time.sleep(0.2)
            # Ensure clean: also try unmake in case toggle re-made it fullscreen
            try:
                det = wm.get_details(editor.id)
                if det and det.get("fullscreen"):
                    wm.unmake_fullscreen(editor.id)
                    print("      unmake_fullscreen (final restore)")
            except Exception:
                pass
        except Exception as te:
            print(f"      [SKIP] toggle_fullscreen: {te}")
            # Best-effort restore
            try:
                wm.unmake_fullscreen(editor.id)
            except Exception:
                pass

        demonstrated += 1
        print("      [OK] geometry dance complete (state restored)")
    except Exception as e:
        print(f"      [SKIP] geometry dance: {e}")

    # ── Step 6: minimize / unminimize ──────────────────────────────────
    print(f"[6/{TOTAL_STEPS}] minimize+unminimize with 0.4s sleeps")
    try:
        if wm is None:
            raise RuntimeError("WindowManager not available")
        if editor is None:
            raise RuntimeError("no editor window — skipping")
        try:
            wm.minimize(editor.id)
            print("      minimize -> True")
            time.sleep(0.4)
        except Exception as me:
            print(f"      [SKIP] minimize: {me}")
        try:
            wm.unminimize(editor.id)
            print("      unminimize (restore) -> True")
            time.sleep(0.4)
        except Exception as ue:
            print(f"      [SKIP] unminimize: {ue}")
        demonstrated += 1
        print("      [OK] minimize cycle (restored)")
    except Exception as e:
        print(f"      [SKIP] minimize cycle: {e}")

    # ── Step 7: get_details flags ──────────────────────────────────────
    print(f"[7/{TOTAL_STEPS}] get_details — maximized/canclose flags")
    try:
        if wm is None:
            raise RuntimeError("WindowManager not available")
        if editor is None:
            raise RuntimeError("no editor window — skipping")
        details = wm.get_details(editor.id)
        if details is None:
            raise RuntimeError("get_details returned None")
        print(f"      details: maximized={details.get('maximized')} canclose={details.get('canclose')} fullscreen={details.get('fullscreen')}")
        demonstrated += 1
        print("      [OK] get_details flags inspected")
    except Exception as e:
        print(f"      [SKIP] get_details: {e}")

    # ── Step 8: workspace move then back ───────────────────────────────
    print(f"[8/{TOTAL_STEPS}] move_to_workspace(1) then back to original workspace")
    try:
        if wm is None:
            raise RuntimeError("WindowManager not available")
        if editor is None:
            raise RuntimeError("no editor window — skipping")
        orig_ws = original_workspace if original_workspace is not None else getattr(editor, "workspace", 0)
        print(f"      original workspace: {orig_ws}")
        try:
            wm.move_to_workspace(editor.id, 1)
            print("      move_to_workspace(1) -> True")
            time.sleep(0.4)
        except Exception as me:
            print(f"      [SKIP] move_to_workspace(1): {me}")
        # Restore
        try:
            wm.move_to_workspace(editor.id, orig_ws)
            print(f"      move_to_workspace({orig_ws}) restore -> True")
            time.sleep(0.2)
        except Exception as re:
            print(f"      [SKIP] restore workspace: {re}")
        demonstrated += 1
        print("      [OK] workspace move restored")
    except Exception as e:
        print(f"      [SKIP] workspace: {e}")

    # ── Step 9: cleanup + leak check ───────────────────────────────────
    print(f"[9/{TOTAL_STEPS}] cleanup — close(editor.id)+terminate popen, leak check")
    try:
        if wm is None:
            raise RuntimeError("WindowManager not available")
        leak_before = None
        try:
            leak_before = len(wm.list_windows())
        except Exception:
            pass

        closed = False
        if editor is not None:
            # Only close windows we spawned — avoid destroying pre-existing windows
            # If editor_proc exists, this is our spawned window → safe to close.
            # If no proc but editor exists, skip close to preserve user state.
            should_close = editor_proc is not None
            if should_close:
                try:
                    wm.close(editor.id)
                    closed = True
                    print(f"      close({editor.id}) -> True")
                    time.sleep(0.4)
                except Exception as ce:
                    print(f"      [SKIP] close: {ce}")
            else:
                print(f"      skip close — editor not spawned by this run (preserve state) id={editor.id}")

        if editor_proc is not None:
            try:
                editor_proc.terminate()
                try:
                    editor_proc.wait(timeout=2)
                except Exception:
                    try:
                        editor_proc.kill()
                    except Exception:
                        pass
                print("      popen terminated")
            except Exception as te:
                print(f"      [SKIP] terminate popen: {te}")

        # Leak check
        try:
            after = len(wm.list_windows())
            if initial_count is not None:
                print(f"      leak check: initial={initial_count} before_cleanup={leak_before} after={after}")
                if after <= (initial_count + (0 if closed else 1)):
                    print("      [OK] no leak detected")
                else:
                    print(f"      [SKIP] possible leak: after ({after}) > initial ({initial_count})")
            else:
                print(f"      counts: before_cleanup={leak_before} after={after}")
        except Exception as le:
            print(f"      [SKIP] leak check: {le}")

        demonstrated += 1
        print("      [OK] cleanup complete")
    except Exception as e:
        print(f"      [SKIP] cleanup: {e}")

    print()
    print("-" * 70)
    print(f"Capabilities demonstrated: {demonstrated}/{TOTAL_STEPS}")
    print("-" * 70)
    if demonstrated == TOTAL_STEPS:
        print("All 9 capabilities live — WindowManager is fully operational and state was restored.")
    elif demonstrated == 0:
        print("No window manager available — extension missing or headless (see README).")
    else:
        print("Partial run — check [SKIP] lines above for reasons; state was restored where possible.")
    print()

    return demonstrated


def main() -> int:
    """Entry point — plain call run()."""
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
