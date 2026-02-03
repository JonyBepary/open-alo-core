#!/usr/bin/env python3
"""
Debug version of minimal example with verbose error output
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "open_alo_core" / "src"))

from open_alo_core import UnifiedRemoteDesktop, Point


def main():
    print("Unified Remote Desktop - Debug Version")
    print("You will see ONE permission dialog\n")

    try:
        with UnifiedRemoteDesktop() as remote:
            # Initialize with both input and capture
            try:
                print("Calling initialize...")
                result = remote.initialize(persist_mode=2, enable_capture=True)
                print(f"Initialize returned: {result}")

                if not result:
                    print("❌ Initialize returned False/None")
                    return 1

            except Exception as e:
                print(f"❌ Exception during initialize: {e}")
                traceback.print_exc()
                return 1

            print("✅ Initialized!")

            # Get screen info
            try:
                width, height = remote.get_screen_size()
                print(f"Screen: {width}x{height}")
            except Exception as e:
                print(f"❌ get_screen_size failed: {e}")
                traceback.print_exc()
                return 1

            # Take screenshot
            try:
                screenshot = remote.capture_screenshot()
                if screenshot:
                    path = Path("/tmp/test_screenshot.png")
                    path.write_bytes(screenshot)
                    print(f"Screenshot: {path}")
            except Exception as e:
                print(f"❌ capture_screenshot failed: {e}")
                traceback.print_exc()

            # Type some text
            try:
                remote.type_text("Hello from unified demo!\n")
                print("Typed text")
            except Exception as e:
                print(f"❌ type_text failed: {e}")
                traceback.print_exc()

            # Move mouse
            try:
                remote.move_mouse(Point(width // 2, height // 2))
                print("Moved mouse")
            except Exception as e:
                print(f"❌ move_mouse failed: {e}")
                traceback.print_exc()
    except Exception as e:
        print(f"❌ Context manager exception: {e}")
        traceback.print_exc()
        return 1

    print("\n✅ Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
