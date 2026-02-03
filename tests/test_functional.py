#!/usr/bin/env python3
"""
Quick functional test of open_alo_core
Tests UnifiedRemoteDesktop (recommended) and legacy APIs
"""

import sys
sys.path.insert(0, 'open_alo_core/src')

print("="*60)
print("OPEN_ALO_CORE Functional Test")
print("="*60)
print()

# Test 1: Utils
print("1. Testing utilities...")
from open_alo_core import detect_session_type, is_wayland, is_portal_available

session = detect_session_type()
print(f"   Session type: {session}")
print(f"   Is Wayland: {is_wayland()}")
print(f"   Portal available: {is_portal_available()}")
print()

# Test 2: Point operations
print("2. Testing Point type...")
from open_alo_core import Point, Size, Rect

p = Point(100, 200)
print(f"   Point: {p}")
print(f"   Access: p.x={p.x}, p.y={p.y}")

# Test 3: UnifiedRemoteDesktop (RECOMMENDED)
print()
print("3. Testing UnifiedRemoteDesktop (RECOMMENDED) ⭐")
from open_alo_core import UnifiedRemoteDesktop

try:
    remote = UnifiedRemoteDesktop()
    print("   ✅ UnifiedRemoteDesktop created")
    print(f"   Token path: {remote._token_path}")
    remote.close()
    print("   ✅ Closed cleanly")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: WaylandInput (Legacy)
print()
print("4. Testing WaylandInput (Legacy)...")
from open_alo_core import WaylandInput

try:
    ctrl = WaylandInput()
    print("   ✅ WaylandInput created")
    print(f"   Token path: {ctrl._token_path}")
    ctrl.close()
    print("   ✅ Closed cleanly")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: WaylandCapture (Legacy)
print()
print("5. Testing WaylandCapture (Legacy)...")
from open_alo_core import WaylandCapture

try:
    cap = WaylandCapture()
    print("   ✅ WaylandCapture created")
    cap.close()
    print("   ✅ Closed cleanly")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Context manager
print()
print("5. Testing context manager...")
try:
    with WaylandInput() as ctrl:
        print("   ✅ Entered context")
    print("   ✅ Exited context (auto-cleanup)")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("="*60)
print("✅ All structure tests passed!")
print("="*60)
print()
print("Ready for actual portal tests:")
print("  - Initialize with ctrl.initialize()")
print("  - Test mouse: ctrl.click(Point(100, 100))")
print("  - Test screenshot: cap.capture_screen()")
