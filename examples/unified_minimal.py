#!/usr/bin/env python3
"""
Minimal Unified Remote Desktop Example
=======================================

Quick test of the single-permission approach.
Shows basic screenshot + input in ~20 lines.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from open_alo_core import UnifiedRemoteDesktop, Point


def main():
    print("Unified Remote Desktop - Minimal Example")
    print("You will see ONE permission dialog\n")

    try:
        with UnifiedRemoteDesktop() as remote:
            # Initialize with both input and capture
            remote.initialize(persist_mode=2, enable_capture=True)

            print("✅ Initialized!")

            # Get screen info
            width, height = remote.get_screen_size()
            print(f"Screen: {width}x{height}")

            # Take screenshot
            screenshot = remote.capture_screenshot()
            if screenshot:
                path = Path("/tmp/test_screenshot.png")
                path.write_bytes(screenshot)
                print(f"Screenshot: {path}")

            # Type some text
            remote.type_text("Hello from unified demo!\n")
            print("Typed text")

            # Move mouse to center
            remote.move_mouse(Point(width // 2, height // 2))
            print("Moved mouse")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
