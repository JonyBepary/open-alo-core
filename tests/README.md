# Tests

This directory contains tests for the modern **open_alo_core** API with UnifiedRemoteDesktop.

## Test Files

### `open_alo_core/test_unified.py` ⭐ **MAIN TEST**

Comprehensive functional test of UnifiedRemoteDesktop:
- Environment validation (Wayland, Portal)
- Type system (Point, Size, Rect)
- UnifiedRemoteDesktop instantiation
- WindowManager integration
- Full integration test with user interaction

**Run:**
```bash
cd /home/jony/OPEN_ALO
/usr/bin/python3 open_alo_core/test_unified.py
```

**What it tests:**
- ✅ Single permission dialog
- ✅ Screen info retrieval
- ✅ Screenshot capture
- ✅ Real-time frame capture
- ✅ Mouse control
- ✅ Keyboard input
- ✅ Keyboard shortcuts
- ✅ Clean shutdown

### `open_alo_core/test_functional.py`

Quick test of all APIs (unified + legacy):
- UnifiedRemoteDesktop (recommended)
- WaylandInput (legacy)
- WaylandCapture (legacy)
- WindowManager
- Type system

**Run:**
```bash
cd /home/jony/OPEN_ALO
/usr/bin/python3 open_alo_core/test_functional.py
```

### `open_alo_core/test_structure.py`

Structure validation test:
- Import validation
- Module structure
- API availability

**Run:**
```bash
cd /home/jony/OPEN_ALO
/usr/bin/python3 open_alo_core/test_structure.py
```

## Running Tests

### Quick Test (No User Interaction)
```bash
# Structure test - validates imports
/usr/bin/python3 open_alo_core/test_structure.py
```

### Full Test (Interactive)
```bash
# Will show permission dialog
/usr/bin/python3 open_alo_core/test_unified.py
```

### All Tests
```bash
# Run all non-interactive tests
/usr/bin/python3 open_alo_core/test_structure.py
/usr/bin/python3 open_alo_core/test_functional.py  # (just instantiation, no portal calls)

# Run interactive test
/usr/bin/python3 open_alo_core/test_unified.py
```

## Expected Output

### test_unified.py Success
```
======================================================================
OPEN_ALO_CORE - UnifiedRemoteDesktop Functional Test
======================================================================

1. Testing utilities...
   Session type: wayland
   Is Wayland: True
   Portal available: True
   ✅ Environment check passed

2. Testing type system...
   Point: Point(x=100, y=200) (x=100, y=200)
   Size: Size(width=1920, height=1080) (width=1920, height=1080)
   Rect: Rect(x=0, y=0, width=1920, height=1080)
   ✅ Types working

3. Testing UnifiedRemoteDesktop instantiation...
   ✅ UnifiedRemoteDesktop created
   Token path: /home/user/.config/open_alo_core/unified_token.json
   ✅ Closed cleanly

4. Testing WindowManager...
   ✅ Found 6 windows
   First window: Terminal

5. Full integration test (INTERACTIVE)
   This will show ONE permission dialog
   Please approve to continue...

   Initializing (approve the dialog)...
   ✅ Initialized successfully

   Testing screen info...
   ✅ Screen size: 1920x1080

   Testing screenshot capture...
   ✅ Screenshot saved: /tmp/unified_test_screenshot.png
   Size: 350,000 bytes

   Testing real-time frame capture...
   ✅ Frame captured: /tmp/unified_test_frame.png
   Size: 350,000 bytes

   Testing mouse movement...
   ✅ Mouse moved to center: Point(x=960, y=540)

   Testing keyboard input...
   ✅ Text typed

   Testing keyboard shortcuts...
   ✅ Ctrl+A executed

   ✅ Session closed cleanly

======================================================================
✅ ALL TESTS PASSED
======================================================================
```

## Troubleshooting

### "Not running on Wayland"
You're on X11. UnifiedRemoteDesktop requires Wayland.

### "Portal not available"
Install XDG Desktop Portal:
```bash
sudo apt install xdg-desktop-portal xdg-desktop-portal-gnome
```

### "WindowManager unavailable"
Install Window Calls extension for GNOME Shell.

### Permission Dialog Doesn't Appear
Check portal is running:
```bash
systemctl --user status xdg-desktop-portal
```

### Screenshot/Frame is Empty
Make sure you selected the **monitor** in the permission dialog, not the webcam.

## Legacy Tests

Legacy tests for the old `open_alo` implementation have been moved to:
```
archive/tests/
```

These tests use the old two-permission approach with `WaylandBackend`, `SmartWaylandBackend`, etc.

See `archive/tests/README.md` for details on legacy tests.

## Writing New Tests

For new tests, use the unified API:

```python
from open_alo_core import UnifiedRemoteDesktop, Point

def test_feature():
    with UnifiedRemoteDesktop() as remote:
        remote.initialize(persist_mode=2, enable_capture=True)

        # Test your feature
        screenshot = remote.capture_screenshot()
        assert screenshot is not None

        remote.click(Point(100, 200))
        # etc
```

## CI/CD Integration

For automated testing without user interaction:

```python
# Skip interactive tests in CI
import os

if os.getenv('CI'):
    print("Skipping interactive tests in CI environment")
    sys.exit(0)
```

Or use mocking:
```python
from unittest.mock import Mock, patch

@patch('open_alo_core.wayland.unified.UnifiedRemoteDesktop')
def test_automated(mock_remote):
    # Test logic without actual portal calls
    pass
```

---

**Test Suite Status:** ✅ Updated for UnifiedRemoteDesktop API
**Last Updated:** February 2026
