#!/usr/bin/env python3
"""
Unified AI Agent Demo - Single Permission Approach
==================================================

This example demonstrates the UnifiedRemoteDesktop class which provides
all AI agent capabilities with a single permission dialog:
- Real-time screen streaming
- Screenshot capture
- Mouse control (click, move)
- Keyboard control (type, shortcuts)
- Screen info (resolution)

Combined with WindowManager for complete automation.

Requirements:
- GNOME on Wayland
- Window Calls extension (for window management)
- GStreamer 1.0 with pipewire plugin
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from open_alo_core import UnifiedRemoteDesktop, WindowManager, Point


def main():
    print("=" * 70)
    print("Unified AI Agent Demo - Single Permission Approach")
    print("=" * 70)
    print()

    # Step 1: Initialize unified remote desktop
    print("Step 1: Initializing unified remote desktop...")
    print("→ You will see ONE permission dialog for both input and screen capture")
    print()

    with UnifiedRemoteDesktop() as remote:
        # Initialize with both capabilities
        if not remote.initialize(persist_mode=2, enable_capture=True):
            print("❌ Failed to initialize remote desktop")
            return 1

        print("✅ Remote desktop initialized successfully!")
        print()

        # Step 2: Get screen info
        print("Step 2: Getting screen information...")
        width, height = remote.get_screen_size()
        print(f"✅ Screen size: {width}x{height}")
        print()

        # Step 3: Take a screenshot
        print("Step 3: Capturing screenshot...")
        screenshot_data = remote.capture_screenshot()
        if screenshot_data:
            output_path = Path("/tmp/unified_screenshot.png")
            output_path.write_bytes(screenshot_data)
            print(f"✅ Screenshot saved to: {output_path}")
            print(f"   Size: {len(screenshot_data):,} bytes")
        else:
            print("❌ Failed to capture screenshot")
        print()

        # Step 4: Window management
        print("Step 4: Demonstrating window management...")
        wm = WindowManager()

        windows = wm.list_windows()
        print(f"✅ Found {len(windows)} windows:")
        for i, win in enumerate(windows[:5], 1):
            print(f"   {i}. {win.title} ({win.wm_class})")
        if len(windows) > 5:
            print(f"   ... and {len(windows) - 5} more")
        print()

        # Step 5: Find and activate a window
        print("Step 5: Finding text editor window...")
        editor = wm.find_window("TextEditor")
        if not editor:
            editor = wm.find_window("gedit")

        if editor:
            print(f"✅ Found: {editor.title}")
            print(f"   Activating window...")
            wm.activate(editor.id)
            time.sleep(0.5)
            print("✅ Window activated")
            print()

            # Step 6: Type text
            print("Step 6: Typing text into window...")
            remote.type_text("Hello from Unified AI Agent!\n", interval=0.05)
            remote.type_text("This is a single-permission demo.\n", interval=0.05)
            time.sleep(0.3)
            print("✅ Text typed successfully")
            print()

            # Step 7: Use keyboard shortcuts
            print("Step 7: Testing keyboard shortcuts...")
            remote.key_combo(["ctrl", "a"])  # Ctrl+A (select all)
            time.sleep(0.2)
            remote.key_combo(["ctrl", "b"])  # Ctrl+B (bold in some editors)
            time.sleep(0.2)
            print("✅ Keyboard shortcuts executed")
            print()

        else:
            print("ℹ️  Text editor not found, skipping typing demo")
            print("   (Try opening GNOME Text Editor or gedit)")
            print()

        # Step 8: Mouse control demo
        print("Step 8: Mouse control demo...")
        center_x, center_y = width // 2, height // 2
        print(f"   Moving mouse to center ({center_x}, {center_y})...")
        remote.move_mouse(Point(center_x, center_y))
        time.sleep(0.3)
        print("✅ Mouse moved")
        print()

        # Step 9: Real-time frame capture
        print("Step 9: Capturing real-time frame...")
        frame_data = remote.get_frame()
        if frame_data:
            frame_path = Path("/tmp/unified_frame.png")
            frame_path.write_bytes(frame_data)
            print(f"✅ Frame captured: {frame_path}")
            print(f"   Size: {len(frame_data):,} bytes")
        else:
            print("❌ Failed to capture frame")
        print()

        # Step 10: Summary
        print("=" * 70)
        print("Demo Complete!")
        print("=" * 70)
        print()
        print("What we demonstrated:")
        print("  ✅ Single permission dialog (vs 2 separate dialogs)")
        print("  ✅ Screen capture (screenshot + real-time frames)")
        print("  ✅ Mouse control (move, click)")
        print("  ✅ Keyboard control (type text, shortcuts)")
        print("  ✅ Window management (list, find, activate)")
        print("  ✅ Screen information (resolution)")
        print()
        print("This is the RECOMMENDED approach for AI agents!")
        print("Use UnifiedRemoteDesktop instead of separate WaylandInput + WaylandCapture")
        print()

    print("✅ Session closed cleanly")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
