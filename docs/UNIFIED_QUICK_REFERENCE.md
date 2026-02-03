# UnifiedRemoteDesktop - Quick Reference

## Import

```python
from open_alo_core import UnifiedRemoteDesktop, Point, WindowManager
```

## Basic Usage

```python
with UnifiedRemoteDesktop() as remote:
    # Initialize (ONE permission dialog)
    remote.initialize(persist_mode=2, enable_capture=True)

    # Use all capabilities
    screenshot = remote.capture_screenshot()
    remote.type_text("Hello")
    remote.move_mouse(Point(100, 200))
```

## API Reference

### Initialization

```python
remote.initialize(
    persist_mode=2,        # 0=never, 1=session, 2=permanent
    enable_capture=True    # Enable screen capture (True for AI agents)
) -> bool
```

### Screen Capture

```python
# Take screenshot
screenshot_bytes = remote.capture_screenshot() -> bytes  # PNG data

# Get real-time frame (for streaming)
frame_bytes = remote.get_frame() -> bytes  # PNG data

# Get screen resolution
width, height = remote.get_screen_size() -> (int, int)
```

### Mouse Control

```python
from open_alo_core import Point

# Move mouse
remote.move_mouse(Point(x=500, y=300))

# Click
remote.click(Point(x=500, y=300), button=1)  # 1=left, 2=middle, 3=right
```

### Keyboard Control

```python
# Type text
remote.type_text("Hello World", interval=0.05)

# Press single key
remote.press_key("enter")  # or key code: 28

# Keyboard shortcut
remote.key_combo(["ctrl", "c"])  # Copy
remote.key_combo(["ctrl", "shift", "t"])  # New terminal tab
```

### Common Key Names

```python
# Modifiers
"ctrl", "shift", "alt", "super"  # (super = Windows/Command key)

# Special keys
"enter", "return", "esc", "escape", "tab", "space"
"backspace", "delete", "insert", "home", "end"
"pageup", "pagedown", "up", "down", "left", "right"

# Function keys
"f1", "f2", ..., "f12"

# Numbers & letters
"a", "b", "c", ..., "z"
"1", "2", ..., "0"
```

## Window Management (Separate, Independent)

```python
from open_alo_core import WindowManager

wm = WindowManager()

# List windows
windows = wm.list_windows()
for w in windows:
    print(f"{w.title} ({w.wm_class})")

# Find window
editor = wm.find_window("TextEditor")  # Searches wm_class and title

# Activate window
wm.activate(editor.id)

# Other operations
wm.maximize(window_id)
wm.minimize(window_id)
wm.close(window_id)
wm.move_resize(window_id, x, y, width, height)
```

## Complete AI Agent Example

```python
from open_alo_core import UnifiedRemoteDesktop, WindowManager, Point
from pathlib import Path

# Setup
wm = WindowManager()
app = wm.find_window("MyApp")
wm.activate(app.id)

# Agent loop
with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)

    while agent_running:
        # 1. Capture current state
        frame = remote.get_frame()
        width, height = remote.get_screen_size()

        # 2. AI decides action
        action = ai_model.process(frame)

        # 3. Execute action
        if action['type'] == 'click':
            remote.click(Point(action['x'], action['y']))

        elif action['type'] == 'type':
            remote.type_text(action['text'])

        elif action['type'] == 'shortcut':
            remote.key_combo(action['keys'])

        elif action['type'] == 'screenshot':
            screenshot = remote.capture_screenshot()
            Path(f"screenshot_{time.time()}.png").write_bytes(screenshot)

        # 4. Wait before next iteration
        time.sleep(0.1)
```

## Error Handling

```python
from open_alo_core.exceptions import PermissionDenied, SessionError, CaptureError

try:
    with UnifiedRemoteDesktop() as remote:
        remote.initialize(enable_capture=True)
        screenshot = remote.capture_screenshot()

except PermissionDenied:
    print("User denied permission")

except SessionError as e:
    print(f"Portal session failed: {e}")

except CaptureError as e:
    print(f"Screen capture failed: {e}")
```

## Tips & Best Practices

### 1. Use Context Manager
```python
# ✅ Good - auto cleanup
with UnifiedRemoteDesktop() as remote:
    remote.initialize()
    # use remote...

# ❌ Bad - manual cleanup required
remote = UnifiedRemoteDesktop()
remote.initialize()
# ... must call remote.close()
```

### 2. Persistent Sessions
```python
# For AI agents, use persist_mode=2
remote.initialize(persist_mode=2)  # Permission saved, no re-auth
```

### 3. Check Initialization
```python
# Initialization raises exceptions on failure
try:
    remote.initialize(enable_capture=True)
except PermissionDenied:
    print("User denied - can't continue")
    return
```

### 4. Screen Size First
```python
# Get screen size before calculating coordinates
width, height = remote.get_screen_size()
center = Point(width // 2, height // 2)
remote.move_mouse(center)
```

### 5. Typing Speed
```python
# Fast typing (for scripts)
remote.type_text("command", interval=0.01)

# Human-like typing (for UI testing)
remote.type_text("Hello", interval=0.1)
```

### 6. Window Activation Delay
```python
# Give window time to focus before typing
wm.activate(window_id)
time.sleep(0.3)  # Important!
remote.type_text("Hello")
```

## Common Patterns

### Pattern: Screenshot & Verify
```python
screenshot = remote.capture_screenshot()
if verify_expected_state(screenshot):
    remote.click(Point(100, 200))
else:
    raise RuntimeError("Unexpected UI state")
```

### Pattern: Type & Submit
```python
remote.type_text("search query")
time.sleep(0.1)
remote.press_key("enter")
```

### Pattern: Select All & Replace
```python
remote.key_combo(["ctrl", "a"])  # Select all
time.sleep(0.05)
remote.type_text("replacement text")
```

### Pattern: Multi-Window Workflow
```python
wm = WindowManager()

# Activate browser
browser = wm.find_window("brave")
wm.activate(browser.id)
time.sleep(0.3)

with UnifiedRemoteDesktop() as remote:
    remote.initialize()

    # Work in browser
    remote.key_combo(["ctrl", "l"])  # Address bar
    remote.type_text("https://example.com\n")
    time.sleep(2)

    # Take screenshot
    screenshot = remote.capture_screenshot()

    # Switch to editor
    editor = wm.find_window("TextEditor")
    wm.activate(editor.id)
    time.sleep(0.3)

    # Paste content
    remote.key_combo(["ctrl", "v"])
```

## Performance Notes

- **Screenshot:** ~100-200ms
- **get_frame():** ~50-100ms (from running stream)
- **Mouse move:** <10ms
- **Key press:** <10ms
- **Type text:** interval × character_count

## Requirements

- GNOME on Wayland
- Window Calls extension (for window management)
- GStreamer 1.0 with pipewire plugin
- Python 3.10+
- PyGObject

## Testing

```bash
# Minimal test (20 lines)
/usr/bin/python3 examples/unified_minimal.py

# Full demo
/usr/bin/python3 examples/unified_ai_agent_demo.py

# Debug version
/usr/bin/python3 examples/unified_debug.py
```

## Troubleshooting

### "No such method SelectSources"
Fixed in current version - uses correct ScreenCast interface for source selection.

### "Failed to initialize"
Check:
1. Running on Wayland (not X11)
2. XDG Desktop Portal installed
3. Permission not denied by user
4. Run with `--verbose` for details

### "cannot unpack non-iterable NoneType" on get_screen_size()
Ensure `enable_capture=True` in `initialize()`.

### Typed text not appearing
1. Check window is focused: `wm.activate(window_id)` + `time.sleep(0.3)`
2. Try slower typing: `interval=0.1`

### Screenshot is blank/black
Portal may not have screen access. Check portal permissions:
```bash
flatpak permissions | grep desktop-portal
```

## Migration from Old API

### Before (Two Dialogs)
```python
with WaylandInput() as input_ctrl:
    input_ctrl.initialize()  # Dialog 1

    with WaylandCapture() as capture:
        capture.initialize()  # Dialog 2

        data = capture.capture_screenshot()
        input_ctrl.type_text("Hello")
```

### After (One Dialog)
```python
with UnifiedRemoteDesktop() as remote:
    remote.initialize(enable_capture=True)  # Dialog 1 only!

    data = remote.capture_screenshot()
    remote.type_text("Hello")
```

Methods have identical signatures - just combine the two classes.

## See Also

- [Complete API Reference](../open_alo_core/API_REFERENCE.md)
- [Migration Guide](./MIGRATION_TO_UNIFIED.md)
- [Implementation Summary](./UNIFIED_REMOTEDESKTOP_SUMMARY.md)
- [Examples](../examples/)

---

**Version:** open_alo_core v0.1.0
**Status:** Production Ready
**Recommended:** For all new AI agent development
