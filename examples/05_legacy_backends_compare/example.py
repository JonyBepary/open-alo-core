#!/usr/bin/env python3
"""
05 — Legacy Backends Compare — the two single-purpose backends vs unified, and when each still wins.

WaylandCapture (ScreenCast one-shot) and WaylandInput (RemoteDesktop input) each
require their own portal dialog and session. UnifiedRemoteDesktop collapses both
into ONE grant. This example shows the trade-offs and the few places where the
single-purpose backends still make sense.

Run:
    python example.py              # safe: no input injected
    python example.py --with-input # actually probes WaylandInput.key_combo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# --- sys.path bootstrap to parents[2]/"src" ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from open_alo_core import WaylandCapture, WaylandInput

BANNER = "OPEN_ALO CAPABILITY SHOWCASE"
TITLE = "05 — Legacy Backends Compare — two single-purpose backends vs unified"
TOTAL_STEPS = 4


# ---------------------------------------------------------------------------
# Comparison table
# ---------------------------------------------------------------------------

def comparison_table() -> List[Tuple[str, str, str]]:
    """
    Return comparison rows (aspect, legacy, unified).

    Each legacy cell mentions BOTH WaylandCapture and WaylandInput so that
    every row mentions all three backend names across its cells (required by
    headless test). Aspects:

      - dialogs required (1 per backend vs 1 total)
      - capture (PNG one-shot vs PNG+raw-RGB streaming)
      - input (none for Capture / full for Input)
      - session lifetime (ephemeral vs persistent + restore_token)
      - recommended-for (kiosk screenshot / input-only automation / agents)
    """
    rows: List[Tuple[str, str, str]] = [
        (
            "dialogs required",
            "WaylandCapture: 1 dialog; WaylandInput: 1 dialog (2 if both)",
            "UnifiedRemoteDesktop: 1 dialog total (RemoteDesktop+ScreenCast)",
        ),
        (
            "capture",
            "WaylandCapture: PNG one-shot (pipewiresrc→pngenc); WaylandInput: none",
            "UnifiedRemoteDesktop: PNG + raw-RGB streaming (appsink)",
        ),
        (
            "input",
            "WaylandCapture: none; WaylandInput: full (click/move/type/keys)",
            "UnifiedRemoteDesktop: full + drag/scroll/swipe/preflight",
        ),
        (
            "session lifetime",
            "WaylandCapture: ephemeral (close after capture); WaylandInput: persistent tokens.json",
            "UnifiedRemoteDesktop: persistent + restore_token (unified_token.json)",
        ),
        (
            "recommended-for",
            "WaylandCapture: kiosk screenshot; WaylandInput: input-only automation",
            "UnifiedRemoteDesktop: agents (single grant, lockstep obs)",
        ),
    ]
    return rows


def _format_table(rows: List[Tuple[str, str, str]]) -> List[str]:
    """Format rows into aligned lines each <=120 chars."""
    headers = ("Aspect", "Legacy (WaylandCapture / WaylandInput)", "UnifiedRemoteDesktop")
    # column widths that guarantee <=120: 18 + 3 + 48 + 3 + 48 = 120
    w_aspect, w_legacy, w_unified = 18, 48, 48

    def _cell(text: str, width: int) -> str:
        if len(text) <= width:
            return text.ljust(width)
        # truncate with ellipsis
        return text[: width - 1] + "…"

    lines: List[str] = []
    # header
    lines.append(f"{_cell(headers[0], w_aspect)} | {_cell(headers[1], w_legacy)} | {_cell(headers[2], w_unified)}")
    lines.append("-" * w_aspect + "-+-" + "-" * w_legacy + "-+-" + "-" * w_unified)
    for aspect, legacy, unified in rows:
        lines.append(f"{_cell(aspect, w_aspect)} | {_cell(legacy, w_legacy)} | {_cell(unified, w_unified)}")
    return lines


# ---------------------------------------------------------------------------
# Live helpers
# ---------------------------------------------------------------------------

def capture_once() -> Optional[Tuple[bytes, int]]:
    """
    One-shot screen capture via WaylandCapture context manager.

    Returns:
        (data, len(data)) on success, None on any exception (portal denied,
        PipeWire unavailable, timeout, etc.).
    """
    try:
        with WaylandCapture() as cap:
            result = cap.capture_screen()
            data: bytes = result.data  # CaptureResult.data
            return (data, len(data))
    except Exception:
        return None


def input_probe(keys: List[str] | None = None) -> bool:
    """
    Probe WaylandInput input path.

    Args:
        keys: key combo to send (default ["ctrl","l"]).

    Returns:
        True if initialize + key_combo succeeded, False on any failure.
        Handles the legacy initialize() returning False (monkeypatched in tests)
        as well as the real impl returning None on success.
    """
    if keys is None:
        keys = ["ctrl", "l"]
    inst: Optional[WaylandInput] = None
    try:
        inst = WaylandInput()
        ret = inst.initialize(persist_mode=0)
        # headless test monkeypatches initialize to return False -> treat as failure
        if ret is False:
            return False
        inst.key_combo(keys)
        return True
    except Exception:
        return False
    finally:
        if inst is not None:
            try:
                inst.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Main flow — 4 steps, [OK]/[SKIP], footer
# ---------------------------------------------------------------------------

def run(skip_live: bool = False, with_input: bool = False) -> int:
    """
    Execute the 4-step showcase.

    Args:
        skip_live: if True, skip live capture (treat as headless).
        with_input: if True, actually run input_probe (requires --with-input).

    Returns:
        Number of demonstrated capabilities (0..TOTAL_STEPS). Table counts as 1.
    """
    # support legacy call run(with_input=True) vs run(skip_live=False)
    # normalize: if caller passed only with_input positionally, handle
    print("=" * 70)
    print(BANNER)
    print("=" * 70)
    print(TITLE)
    print()

    demonstrated = 0

    # ── Step 1: comparison table ──────────────────────────────────────
    print(f"[1/{TOTAL_STEPS}] comparison_table() — legacy vs unified")
    try:
        rows = comparison_table()
        lines = _format_table(rows)
        for line in lines:
            print(f"      {line}")
        # also explain aspects
        print("      note: dialogs 1 per backend vs 1 total; capture PNG one-shot vs PNG+raw-RGB")
        print("            input none/full; session ephemeral vs persistent+restore_token")
        demonstrated += 1
        print("      [OK] table rendered")
    except Exception as e:
        print(f"      [SKIP] comparison_table failed: {e}")

    # ── Step 2: capture_once ──────────────────────────────────────────
    print(f"[2/{TOTAL_STEPS}] capture_once() — WaylandCapture one-shot PNG")
    if skip_live:
        print("      [SKIP] skip_live=True — not attempting portal")
    else:
        try:
            data: Optional[bytes] = None
            source_type = "unknown"
            size: Tuple[int, int] = (0, 0)
            n = 0
            with WaylandCapture() as cap:
                result = cap.capture_screen()
                data = result.data
                source_type = result.source_type
                size = result.size
                n = len(data)

            if data is None or n == 0:
                raise RuntimeError("capture returned empty")

            out = Path("/tmp/open_alo_05_legacy.png")
            out.write_bytes(data)
            print(f"      [OK] {n:,} bytes source_type={source_type} size={size} -> {out}")
            print("      detail: pipewiresrc path={node} num-buffers=1 ! videoconvert ! video/x-raw,format=RGB ! pngenc ! appsink (10s wall clock)")
            demonstrated += 1
        except Exception as e:
            print(f"      [SKIP] portal denied / no capture: {e}")

    # ── Step 3: input_probe ───────────────────────────────────────────
    print(f"[3/{TOTAL_STEPS}] input_probe() — WaylandInput key_combo (opt-in)")
    if not with_input:
        print("      [SKIP] pass --with-input to actually inject keys (typing unprompted is rude)")
        print("      note: would run WaylandInput().initialize(persist_mode=0) then key_combo(['ctrl','l'])")
    else:
        try:
            ok = input_probe(keys=["ctrl", "l"])
            if ok:
                demonstrated += 1
                print("      [OK] WaylandInput key_combo ['ctrl','l'] succeeded")
                print("      detail: NotifyKeyboardKeysym Shift-aware lowercasing; _notify_pointer_motion_absolute oa{sv}udd fallback oa{sv}dd")
            else:
                print("      [SKIP] input_probe returned False (portal denied / not on Wayland)")
        except Exception as e:
            print(f"      [SKIP] input_probe failed: {e}")

    # ── Step 4: guidance ──────────────────────────────────────────────
    print(f"[4/{TOTAL_STEPS}] guidance — when to use each backend")
    try:
        print("      WaylandCapture  -> kiosk screenshot, one-shot PNG, ephemeral close() after each capture_screen")
        print("      WaylandInput    -> input-only automation, full input, persistent tokens.json")
        print("      UnifiedRemoteDesktop -> agents -> single dialog, persistent unified_token.json, PNG+raw-RGB streaming")
        print("      agents -> UnifiedRemoteDesktop (one grant, lockstep observation, preflight, drag/scroll)")
        demonstrated += 1
        print("      [OK] guidance printed")
    except Exception as e:
        print(f"      [SKIP] guidance failed: {e}")

    print()
    print("-" * 70)
    print(f"Capabilities demonstrated: {demonstrated}/{TOTAL_STEPS}")
    print("-" * 70)
    if demonstrated == TOTAL_STEPS:
        print("All 4 capabilities — legacy vs unified trade-offs demonstrated.")
    elif demonstrated == 0:
        print("No portal available — running headless (see README).")
    else:
        print("Partial — check [SKIP] lines above.")
    print()
    return demonstrated


def main() -> int:
    parser = argparse.ArgumentParser(description=TITLE)
    parser.add_argument("--with-input", action="store_true", help="actually probe WaylandInput key injection (default: skip)")
    parser.add_argument("--skip-live", action="store_true", help="skip live capture even if portal available")
    args = parser.parse_args()

    try:
        run(skip_live=args.skip_live, with_input=args.with_input)
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
