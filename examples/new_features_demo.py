#!/usr/bin/env python3
"""
Open ALO - New Features Demo
============================

Demonstrates the new scroll, drag, and convenience methods.
All methods use the UnifiedRemoteDesktop API.

Usage:
    python3 examples/new_features_demo.py

Requirements:
    - Wayland (GNOME, KDE, Sway)
    - xdg-desktop-portal + xdg-desktop-portal-gnome
    - Window Calls extension (for window management)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from open_alo_core import (
    UnifiedRemoteDesktop,
    WindowManager,
    Point,
)


def main():
    # ========== UNIFIED REMOTE DESKTOP ==========
    print("=" * 70)
    print("Open ALO - New Features Demo")
    print("=" * 70)

    try:
        with UnifiedRemoteDesktop() as desktop:
            print("\n1. Initializing (approve the dialog)...")
            desktop.initialize(persist_mode=2, enable_capture=True)

            screen = desktop.get_screen_size()
            print(f"   Screen size: {screen}")
            center = (
                Point(screen[0] // 2, screen[1] // 2) if screen else Point(500, 500)
            )

            # Config properties
            print("\n2. Config Properties")
            print(f"   Default pause: {desktop.pause}s")
            desktop.pause = 0.02
            print(f"   Set pause to: {desktop.pause}s")
            print(f"   Fail-safe mode: {desktop.fail_safe}")
            print(f"   Touch mode: {desktop.touch_mode}")

            # Scroll
            print("\n3. Scroll")
            print("   Scrolling down 3 clicks...")
            desktop.scroll(-3)
            print("   Scrolling up 5 clicks...")
            desktop.scroll(5)
            print("   Scrolling horizontally right...")
            desktop.hscroll(3)
            print("   Smooth scroll (touchpad-style)...")
            desktop.smooth_scroll(dy=-50)

            # Drag
            print("\n4. Drag Operations")
            drag_start = Point(center.x - 100, center.y)
            drag_end = Point(center.x + 100, center.y)
            print(f"   Dragging from {drag_start} to {drag_end}...")
            desktop.drag(drag_start, drag_end, duration=0.3)
            print("   Swipe (smooth drag with steps)...")
            desktop.swipe(center, Point(center.x, center.y + 200), duration=0.5)

            # Convenience methods
            print("\n5. Convenience Methods")
            print("   Double-clicking...")
            desktop.double_click(center)
            print("   Moving mouse relative (+50, +50)...")
            desktop.move_mouse_relative(50, 50)

            # Hold key context manager
            print("\n6. Key Hold (Shift+Click)")
            print("   Holding Shift while clicking...")
            with desktop.hold_key("Shift"):
                desktop.click(center)

            # Press multiple keys
            print("\n7. Press Keys Sequence")
            desktop.press_keys(["a", "b", "c"])

            # Take a screenshot to verify everything worked
            print("\n8. Screenshot (verification)")
            screenshot = desktop.capture_screenshot()
            if screenshot:
                output = Path("/tmp/new_features_demo.png")
                output.write_bytes(screenshot)
                print(f"   Screenshot saved: {output} ({len(screenshot)} bytes)")

    except Exception as e:
        print(f"   Error: {e}")
        return 1

    # ========== WINDOW MANAGER ==========
    print("\n" + "=" * 70)
    print("Window Manager - Fullscreen Demo")
    print("=" * 70)

    try:
        wm = WindowManager()
        windows = wm.list_windows()
        if windows:
            first = windows[0]
            print(f"\n   First window: {first.wm_class} (id: {first.id})")
            print("   Making window fullscreen...")
            wm.make_fullscreen(first.id)
            print("   Toggling fullscreen off...")
            wm.toggle_fullscreen(first.id)
        else:
            print("   No windows found")
    except Exception as e:
        print(f"   Window manager error: {e}")

    print("\nDemo complete!")
    print("New features demonstrated: scroll, hscroll, smooth_scroll, drag, swipe,")
    print("hold_key, double_click, move_mouse_relative, press_keys, pause,")
    print("fail_safe, touch_mode, make_fullscreen, toggle_fullscreen")

    return 0


if __name__ == "__main__":
    sys.exit(main())
