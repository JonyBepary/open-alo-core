# Migration Guide: Two-Permission → Unified API

## Overview

The **UnifiedRemoteDesktop** class provides the same capabilities as `WaylandInput` + `WaylandCapture` but with a **single permission dialog**, improving user experience significantly.

This is especially important for AI agents that need both screen access and input control.

## Why Migrate?

### Old Approach (Two Permissions)
```python
from open_alo_core import WaylandInput, WaylandCapture

# First permission dialog
with WaylandInput() as input_ctrl:
    input_ctrl.initialize()

    # Second permission dialog
    with WaylandCapture() as capture:
        capture.initialize()

        # Now you can use both
        screenshot = capture.capture_screenshot()
        input_ctrl.type_text("Hello")
```

**Problems:**
- ❌ Two separate permission dialogs (annoying UX)
- ❌ Two portal sessions to manage
- ❌ More complex code
- ❌ Harder to recover if one fails

### New Approach (Single Permission)
```python
from open_alo_core import UnifiedRemoteDesktop

# Single permission dialog
with UnifiedRemoteDesktop() as remote:
    remote.initialize(enable_capture=True)

    # Both capabilities available immediately
    screenshot = remote.capture_screenshot()
    remote.type_text("Hello")
```

**Benefits:**
- ✅ One permission dialog (better UX)
- ✅ Single session (simpler)
- ✅ Less code
- ✅ Same approach as RustDesk, AnyDesk, etc.

## API Mapping

### Initialization

**Old:**
```python
from open_alo_core import WaylandInput, WaylandCapture

input_ctrl = WaylandInput()
input_ctrl.initialize(persist_mode=2)

capture = WaylandCapture()
capture.initialize(persist_mode=2)
```

**New:**
```python
from open_alo_core import UnifiedRemoteDesktop

remote = UnifiedRemoteDesktop()
remote.initialize(
    persist_mode=2,        # Persistent session (optional)
    enable_capture=True    # Enable screen capture
)
```

### Mouse Control

**Old:**
```python
from open_alo_core import Point

input_ctrl.click(Point(100, 200), button=1)
input_ctrl.move_mouse(Point(500, 500))
```

**New:**
```python
from open_alo_core import Point

remote.click(Point(100, 200), button=1)
remote.move_mouse(Point(500, 500))
```

✅ **Same API** - no changes needed!

### Keyboard Control

**Old:**
```python
# Type text
input_ctrl.type_text("Hello World", interval=0.05)

# Press single key
input_ctrl.press_key(28)  # Enter

# Keyboard shortcut
input_ctrl.key_combo([29, 45])  # Ctrl+X
```

**New:**
```python
# Type text
remote.type_text("Hello World", interval=0.05)

# Press single key
remote.press_key(28)  # Enter

# Keyboard shortcut
remote.key_combo([29, 45])  # Ctrl+X
```

✅ **Same API** - no changes needed!

### Screen Capture

**Old:**
```python
# Screenshot
screenshot_data = capture.capture_screenshot()

# Real-time frame
frame_data = capture.get_frame()

# Screen info
width, height = capture.get_screen_size()
```

**New:**
```python
# Screenshot
screenshot_data = remote.capture_screenshot()

# Real-time frame
frame_data = remote.get_frame()

# Screen info
width, height = remote.get_screen_size()
```

✅ **Same API** - no changes needed!

### Context Managers

**Old:**
```python
with WaylandInput() as input_ctrl:
    input_ctrl.initialize()
    with WaylandCapture() as capture:
        capture.initialize()
        # Use both...
```

**New:**
```python
with UnifiedRemoteDesktop() as remote:
    remote.initialize(enable_capture=True)
    # Use both...
```

Much cleaner! ✅

## Migration Examples

### Example 1: Simple Screenshot + Type

**Before:**
```python
from open_alo_core import WaylandInput, WaylandCapture
from pathlib import Path

def screenshot_and_type():
    with WaylandInput() as input_ctrl:
        if not input_ctrl.initialize():
            return

        with WaylandCapture() as capture:
            if not capture.initialize():
                return

            # Take screenshot
            data = capture.capture_screenshot()
            Path("/tmp/screenshot.png").write_bytes(data)

            # Type something
            input_ctrl.type_text("Screenshot saved!")
```

**After:**
```python
from open_alo_core import UnifiedRemoteDesktop
from pathlib import Path

def screenshot_and_type():
    with UnifiedRemoteDesktop() as remote:
        if not remote.initialize(enable_capture=True):
            return

        # Take screenshot
        data = remote.capture_screenshot()
        Path("/tmp/screenshot.png").write_bytes(data)

        # Type something
        remote.type_text("Screenshot saved!")
```

**Changes:**
- Single import instead of two
- One `initialize()` call instead of two
- One context manager instead of nested
- Same methods work identically

### Example 2: AI Agent Loop

**Before:**
```python
from open_alo_core import WaylandInput, WaylandCapture

def ai_agent_loop():
    with WaylandInput() as input_ctrl:
        input_ctrl.initialize(persist_mode=2)

        with WaylandCapture() as capture:
            capture.initialize(persist_mode=2)

            while True:
                # Get current screen
                frame = capture.get_frame()

                # AI processes frame...
                action = ai_model.decide(frame)

                # Execute action
                if action['type'] == 'click':
                    input_ctrl.click(action['point'])
                elif action['type'] == 'type':
                    input_ctrl.type_text(action['text'])
```

**After:**
```python
from open_alo_core import UnifiedRemoteDesktop

def ai_agent_loop():
    with UnifiedRemoteDesktop() as remote:
        remote.initialize(persist_mode=2, enable_capture=True)

        while True:
            # Get current screen
            frame = remote.get_frame()

            # AI processes frame...
            action = ai_model.decide(frame)

            # Execute action
            if action['type'] == 'click':
                remote.click(action['point'])
            elif action['type'] == 'type':
                remote.type_text(action['text'])
```

**Benefits:**
- Simpler initialization
- One permission dialog at start
- No nested context managers
- Same loop logic

### Example 3: With Window Management

**Before:**
```python
from open_alo_core import WaylandInput, WaylandCapture, WindowManager

def automate_app(app_name):
    wm = WindowManager()

    # Find and activate window
    window = wm.find_window(wm_class=app_name)
    if window:
        wm.activate(window.id)

    # Now control it
    with WaylandInput() as input_ctrl:
        input_ctrl.initialize()

        with WaylandCapture() as capture:
            capture.initialize()

            # Take screenshot
            capture.capture_screenshot()

            # Type
            input_ctrl.type_text("Hello")
```

**After:**
```python
from open_alo_core import UnifiedRemoteDesktop, WindowManager

def automate_app(app_name):
    wm = WindowManager()

    # Find and activate window
    window = wm.find_window(wm_class=app_name)
    if window:
        wm.activate(window.id)

    # Now control it
    with UnifiedRemoteDesktop() as remote:
        remote.initialize(enable_capture=True)

        # Take screenshot
        remote.capture_screenshot()

        # Type
        remote.type_text("Hello")
```

**Note:** WindowManager still works the same - it's independent of input/capture!

## Step-by-Step Migration

1. **Update Imports**
   ```python
   # Old
   from open_alo_core import WaylandInput, WaylandCapture

   # New
   from open_alo_core import UnifiedRemoteDesktop
   ```

2. **Replace Initialization**
   ```python
   # Old
   input_ctrl = WaylandInput()
   input_ctrl.initialize(persist_mode=2)

   capture = WaylandCapture()
   capture.initialize(persist_mode=2)

   # New
   remote = UnifiedRemoteDesktop()
   remote.initialize(persist_mode=2, enable_capture=True)
   ```

3. **Update Method Calls**
   ```python
   # Old
   input_ctrl.click(point)
   input_ctrl.type_text(text)
   capture.capture_screenshot()

   # New
   remote.click(point)
   remote.type_text(text)
   remote.capture_screenshot()
   ```

4. **Simplify Context Managers**
   ```python
   # Old
   with WaylandInput() as input_ctrl:
       input_ctrl.initialize()
       with WaylandCapture() as capture:
           capture.initialize()
           # ...

   # New
   with UnifiedRemoteDesktop() as remote:
       remote.initialize(enable_capture=True)
       # ...
   ```

## Testing Your Migration

Run the examples to verify:

```bash
# Test basic functionality
/usr/bin/python3 examples/unified_minimal.py

# Test full workflow
/usr/bin/python3 examples/unified_ai_agent_demo.py
```

## Backwards Compatibility

The old API (`WaylandInput` + `WaylandCapture`) still works and will continue to be supported. However:

- **Recommended for new code:** `UnifiedRemoteDesktop`
- **Legacy code:** Can continue using old API
- **Migration timeline:** No forced migration, but unified approach preferred

## FAQ

**Q: Do I need to migrate immediately?**
A: No, the old API still works. Migrate when convenient.

**Q: What if I only need input, not capture?**
A: You can still use `WaylandInput` alone, or use `UnifiedRemoteDesktop` with `enable_capture=False`.

**Q: Does this work on X11?**
A: No, this is Wayland-only (like the old API).

**Q: Can I mix both APIs?**
A: Not recommended. Pick one approach per session.

**Q: What about performance?**
A: Unified approach is actually more efficient (one portal session instead of two).

## Technical Details

The `UnifiedRemoteDesktop` class uses the XDG RemoteDesktop portal which inherits from the ScreenCast portal. This allows:

1. Calling `SelectDevices()` for input capabilities
2. Calling `SelectSources()` for capture capabilities
3. Both on the same portal session
4. Single permission dialog for user

This is the same approach used by:
- RustDesk
- AnyDesk
- Chrome Remote Desktop
- Other professional remote desktop solutions

See [UNIFIED_REMOTEDESKTOP_APPROACH.md](./UNIFIED_REMOTEDESKTOP_APPROACH.md) for implementation details.

## Support

If you encounter issues during migration:

1. Check examples in `examples/unified_*.py`
2. Compare with old examples in `examples/agent_example.py`
3. Review API reference in `open_alo_core/API_REFERENCE.md`
4. File an issue with your specific use case

## Summary

**Key Takeaway:** The unified API provides the same functionality with better UX and simpler code. The method signatures are identical, so migration is mostly about simplifying initialization and context management.

✅ Same methods
✅ Same parameters
✅ Same behavior
✅ Better UX (one dialog)
✅ Simpler code
