#!/usr/bin/env python3
"""
Quick functional test of open_alo_core
Tests UnifiedRemoteDesktop (recommended) and legacy APIs
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main() -> int:
    print("=" * 60)
    print("OPEN_ALO_CORE Functional Test")
    print("=" * 60)
    print()

    failed = False

    # Test 1: Utils
    print("1. Testing utilities...")
    try:
        from open_alo_core import detect_session_type, is_wayland

        session = detect_session_type()
        print(f"   Session type: {session}")
        print(f"   Is Wayland: {is_wayland()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed = True
    print()

    # Test 2: Point operations
    print("2. Testing Point type...")
    try:
        from open_alo_core import Point, Rect, Size

        p = Point(100, 200)
        print(f"   Point: {p}")
        print(f"   Access: p.x={p.x}, p.y={p.y}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed = True

    # Test 3: UnifiedRemoteDesktop (RECOMMENDED)
    print()
    print("3. Testing UnifiedRemoteDesktop (RECOMMENDED) ⭐")
    try:
        from open_alo_core import UnifiedRemoteDesktop

        remote = UnifiedRemoteDesktop()
        print("   ✅ UnifiedRemoteDesktop created")
        print(f"   Token path: {remote._token_path}")
        remote.close()
        print("   ✅ Closed cleanly")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed = True

    # Test 4: WaylandInput (Legacy)
    print()
    print("4. Testing WaylandInput (Legacy)...")
    try:
        from open_alo_core import WaylandInput

        ctrl = WaylandInput()
        print("   ✅ WaylandInput created")
        print(f"   Token path: {ctrl._token_path}")
        ctrl.close()
        print("   ✅ Closed cleanly")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed = True

    # Test 5: WaylandCapture (Legacy)
    print()
    print("5. Testing WaylandCapture (Legacy)...")
    try:
        from open_alo_core import WaylandCapture

        cap = WaylandCapture()
        print("   ✅ WaylandCapture created")
        cap.close()
        print("   ✅ Closed cleanly")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed = True

    # Test 6: Context manager
    print()
    print("6. Testing context manager...")
    try:
        from open_alo_core import WaylandInput

        with WaylandInput() as ctrl:
            print("   ✅ Entered context")
        print("   ✅ Exited context (auto-cleanup)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed = True

    print()
    print("=" * 60)
    if failed:
        print("❌ Some functional tests failed!")
        print("=" * 60)
        return 1

    print("✅ All structure tests passed!")
    print("=" * 60)
    print()
    print("Ready for actual portal tests:")
    print("  - Initialize with ctrl.initialize()")
    print("  - Test mouse: ctrl.click(Point(100, 100))")
    print("  - Test screenshot: cap.capture_screen()")
    return 0


if __name__ == "__main__":
    sys.exit(main())

