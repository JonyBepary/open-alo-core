#!/usr/bin/env python3
"""
Portal-in-VM smoke test — proves Wayland + portal + PipeWire plumbing before
you build anything on top (host, nested Weston, or container).

Modes:
  host    — this real Wayland session (positive control)
  nested  — headless Weston on :wayland-test + pipewire + xdg-desktop-portal-wlr/gnome
  container — bind-mounted XDG_RUNTIME_DIR/WAYLAND_DISPLAY + DBus (documented, not auto)

Pass criteria (fail-closed): screen size >0, PNG with magic, injected motion ok,
and (if available) window-actions List.

Usage:
  python tools/portal_smoke.py --mode host
  python tools/portal_smoke.py --mode nested  # needs weston, pipewire, portal impl
  WAYLAND_DISPLAY=wayland-test python tools/portal_smoke.py --mode host

Allocates no persistent session (persist_mode=0) so it never caches a bad token in
your real unified_token.json — override with --token-path if you want persistence.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

PNG_MAGIC = b"\x89PNG"

def _check(cmd, **kw):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=kw.pop("timeout", 5), **kw)
        return r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return False, str(e)

def preflight(args) -> dict:
    out = {"mode": args.mode, "wayland_display": os.environ.get("WAYLAND_DISPLAY",""), "xdg_runtime": os.environ.get("XDG_RUNTIME_DIR",""),
           "xdg_session_type": os.environ.get("XDG_SESSION_TYPE",""), "checks": []}
    def add(name, ok, detail=""):
        out["checks"].append({"name": name, "ok": ok, "detail": detail[:400]})

    # X11 vs Wayland
    add("WAYLAND_DISPLAY set", bool(os.environ.get("WAYLAND_DISPLAY")), os.environ.get("WAYLAND_DISPLAY","(empty)"))
    add("XDG_SESSION_TYPE wayland?", os.environ.get("XDG_SESSION_TYPE")=="wayland", os.environ.get("XDG_SESSION_TYPE",""))

    # portal bus
    try:
        import gi
        gi.require_version("Gio","2.0"); gi.require_version("GLib","2.0")
        from gi.repository import Gio, GLib  # type: ignore
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        v = bus.call_sync("org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","NameHasOwner",
                          GLib.Variant("(s)",("org.freedesktop.portal.Desktop",)), None, Gio.DBusCallFlags.NONE, 500, None)
        has_portal = bool(v.get_child_value(0).get_boolean()) if v else False
        add("portal bus NameHasOwner", has_portal, "org.freedesktop.portal.Desktop present" if has_portal else "not present")
        # also check RemoteDesktop interface exists via introspect
        out["_bus"] = bus  # keep for later
    except Exception as e:
        add("portal bus NameHasOwner", False, str(e))

    # pipewire
    ok, detail = _check(["pw-cli","info"], timeout=2)
    add("pipewire pw-cli", ok, detail[:200] if ok else detail[:300])

    # window-actions extension (optional)
    ok, detail = _check(["gdbus","call","--session","--dest","org.gnome.Shell","--object-path","/org/gnome/Shell/Extensions/Windows","--method","org.gnome.Shell.Extensions.Windows.List"], timeout=3)
    # gdbus returns "(true, '[]')" on success even empty; failure is non-zero
    add("window-actions List", ok, detail[:300])

    # weston presence (for nested mode guidance)
    ok,_ = _check(["which","weston"], timeout=2)
    add("weston binary present", ok, "found" if ok else "not found — nested mode needs: sudo apt install weston pipewire xdg-desktop-portal-wlr")

    return out

def run_host_smoke(args, tmp_token: Path) -> int:
    # Import here so preflight can run even without open_alo installed
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from open_alo_core import UnifiedRemoteDesktop, is_portal_available
    from open_alo_core.utils import is_pipewire_available

    print("== host smoke: UnifiedRemoteDesktop (persist_mode=0, enable_capture=True) ==")
    print(f"   is_portal_available()={is_portal_available()}  is_pipewire_available()={is_pipewire_available()}")
    print(f"   token_path={tmp_token} (ephemeral, will be removed)")
    print("   → initialize() will show ONE portal dialog if no cached token; approve to continue.")
    print("     (Run with --no-input if you only want the preflight checks)\n")
    if args.no_input:
        print("   --no-input: stopping before portal dialog.")
        return 0

    d = UnifiedRemoteDesktop(token_path=tmp_token)
    try:
        t0 = time.monotonic_ns()
        d.initialize(persist_mode=0, enable_capture=True)
        init_ms = (time.monotonic_ns() - t0)//1_000_000
        print(f"   initialize: OK in {init_ms}ms  session={d._session_handle[:40] if d._session_handle else '(none)'}...")

        # screen size
        sz = d.get_screen_size()
        print(f"   get_screen_size: {sz}")
        if not sz or sz[0]<=0 or sz[1]<=0:
            print("   FAIL: screen size invalid"); return 1

        # capture via new harness API if present, else fallback
        png = None
        ts = None
        if hasattr(d, "capture_observation"):
            obs = d.capture_observation()  # type: ignore
            png = obs.get("png") or obs.get("data")
            ts = obs.get("timestamp_ns")
            print(f"   capture_observation: {len(png) if png else 0} bytes  ts={ts}")
        else:
            png = d.capture_screenshot()
            print(f"   capture_screenshot: {len(png) if png else 0} bytes (legacy API)")

        if not png or png[:4] != PNG_MAGIC:
            print(f"   FAIL: PNG magic mismatch: {png[:8]!r}" if png else "   FAIL: no png"); return 1
        print(f"   PNG magic OK  ({len(png)} bytes)")

        # injected motion — absolute (needs stream) with fail-closed semantics
        from open_alo_core.types import Point
        # small nudge inside screen
        cx, cy = sz[0]//2, sz[1]//2
        try:
            d.move_mouse(Point(cx+1, cy))
            print(f"   move_mouse absolute to ({cx+1},{cy}): OK")
        except Exception as e:
            print(f"   move_mouse absolute: FAIL (fail-closed, as intended when stream missing): {e}")
            # relative fallback should still work
            d.move_mouse_relative(1, 0)
            print("   move_mouse_relative(1,0): OK (relative fallback)")

        # non-blocking frame
        f = d.get_frame()
        print(f"   get_frame (non-blocking): {'%d bytes' % len(f) if f else 'None (pipeline warming — OK)'}")

        print("\n== SMOKE PASS: portal + PipeWire + injection all live ==")
        return 0
    except Exception as e:
        print(f"\n== SMOKE FAIL: {e} ==")
        import traceback; traceback.print_exc()
        print("\nHints:")
        print("  - If you denied the portal dialog, re-run and approve it.")
        print("  - For headless/CI, use --mode nested with a headless Weston + pipewire + portal impl (see docs/HARNESS_HARDENING_SCOPE.md §5).")
        print("  - Xvfb will always fail here (X11-only, no portals) — use Weston headless, not Xvfb.")
        return 1
    finally:
        try: d.close()
        except Exception: pass
        try:
            if tmp_token.exists(): tmp_token.unlink()
            if tmp_token.parent.exists() and not any(tmp_token.parent.iterdir()):
                tmp_token.parent.rmdir()
        except Exception:
            pass

def main():
    p = argparse.ArgumentParser(description="Portal-in-VM smoke test")
    p.add_argument("--mode", choices=["host","nested","container"], default="host")
    p.add_argument("--no-input", action="store_true", help="only preflight, don't show portal dialog")
    p.add_argument("--token-path", type=Path, help="override ephemeral token path")
    args = p.parse_args()

    print(f"Portal smoke — mode={args.mode}  WAYLAND_DISPLAY={os.environ.get('WAYLAND_DISPLAY','')}  XDG_RUNTIME_DIR={os.environ.get('XDG_RUNTIME_DIR','')}\n")
    pf = preflight(args)
    for c in pf["checks"]:
        mark = "PASS" if c["ok"] else ("WARN" if "window-actions" in c["name"] or "weston" in c["name"] else "FAIL")
        print(f"  [{mark:4s}] {c['name']:30s}  {c['detail'][:80]}")
    print()
    # critical fails
    must = [c for c in pf["checks"] if c["name"] in ("WAYLAND_DISPLAY set","portal bus NameHasOwner")]
    if any(not c["ok"] for c in must):
        print("Preflight FAIL: Wayland/portal not available in this environment.")
        print("  → On Xvfb this is expected (X11 has no portals). Switch to host or nested Weston per docs.")
        return 2

    if args.mode in ("nested","container"):
        print(f"Mode {args.mode} selected — see docs/HARNESS_HARDENING_SCOPE.md §5 for the exact weston + pipewire + portal launch recipe.")
        print("Running host preflight only in this invocation; launch the nested compositor first, then re-run with WAYLAND_DISPLAY=wayland-test.")
        return 0 if all(c["ok"] for c in must) else 2

    tmp = args.token_path or (Path("/tmp") / f"open_alo_smoke_{os.getpid()}.json")
    return run_host_smoke(args, tmp)

if __name__ == "__main__":
    raise SystemExit(main())
