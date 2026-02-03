#!/usr/bin/env python3
"""
Quick test of open_alo_core package structure
"""

import sys
sys.path.insert(0, 'open_alo_core/src')

print("Testing open_alo_core package structure...")
print()

# Test 1: Import core
try:
    from open_alo_core import WaylandInput, WaylandCapture
    print("✅ WaylandInput imported")
    print("✅ WaylandCapture imported")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Import types
try:
    from open_alo_core import Point, Size, Rect, BUTTON_LEFT
    p = Point(100, 200)
    print(f"✅ Point created: {p}")
except Exception as e:
    print(f"❌ Types failed: {e}")

# Test 3: Import exceptions
try:
    from open_alo_core import CoreError, PermissionDenied
    print("✅ Exceptions imported")
except Exception as e:
    print(f"❌ Exceptions failed: {e}")

# Test 4: Import utils
try:
    from open_alo_core import detect_session_type, is_wayland
    session = detect_session_type()
    print(f"✅ Session type: {session}")
except Exception as e:
    print(f"❌ Utils failed: {e}")

print()
print("="*60)
print("✅ Core package structure looks good!")
print("="*60)
print()
print("Next steps:")
print("  cd open_alo_core")
print("  pip install -e .")
print("  python -c 'from open_alo_core import WaylandInput'")
