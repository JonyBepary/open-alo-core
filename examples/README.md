# OPEN_ALO Examples

This directory contains examples using the modern API from **open_alo_core**.

## 🚀 Quick Start

```bash
# Minimal example - Quick start with all features
/usr/bin/python3 examples/unified_minimal.py

# Comprehensive demo - Full AI agent workflow
/usr/bin/python3 examples/unified_ai_agent_demo.py

# Window management - Find, activate, control windows
/usr/bin/python3 examples/window_management_demo.py

# Desktop overview with window positions
/usr/bin/python3 examples/show_desktop_ui_tree.py

# AT-SPI accessibility tree for focused window
/usr/bin/python3 examples/show_desktop_ui_tree_advanced.py
```

---

## Available Examples

### unified_minimal.py ⭐ **BEST STARTING POINT**

Minimal example (~20 lines) showing single-permission approach:
- Screenshot capture
- Keyboard typing
- Mouse movement
- Screen info

**Features:**
- ✅ ONE permission dialog (not two)
- ✅ Real-time screen streaming + screenshots
- ✅ Mouse + keyboard control
- ✅ Persistent sessions (no re-authorization)

```bash
/usr/bin/python3 examples/unified_minimal.py
```

### unified_ai_agent_demo.py 🎯 **COMPREHENSIVE DEMO**

Complete AI agent workflow demonstration:
- Single permission dialog
- Real-time frame capture
- Screenshot capture
- Window management integration
- Mouse control (move, click)
- Keyboard control (type, shortcuts)
- Screen information

```bash
/usr/bin/python3 examples/unified_ai_agent_demo.py
```

### unified_debug.py 🔧 **TROUBLESHOOTING**

Debug version with verbose error reporting:
- Detailed exception traces
- Step-by-step execution
- Helpful for diagnosing issues

```bash
/usr/bin/python3 examples/unified_debug.py
```

### window_management_demo.py 🪟 **WINDOW CONTROL**

Demonstrates the WindowManager API:
- List all windows
- Find specific windows
- Activate, maximize, minimize
- Move and resize
- Workspace management

```bash
/usr/bin/python3 examples/window_management_demo.py
```

### show_desktop_ui_tree.py 🖥️ **DESKTOP OVERVIEW**

Lists all windows with positions, sizes, and workspace info:
- Screen resolution
- All windows with WM class and coordinates
- Focused window detection

```bash
/usr/bin/python3 examples/show_desktop_ui_tree.py
```

### show_desktop_ui_tree_advanced.py 🌳 **ACCESSIBILITY TREE**

Full AT-SPI accessibility tree for any focused window:
- Recursive tree traversal via pyatspi
- Window states (enabled, visible, focused)
- Supports all GTK/Qt applications

```bash
/usr/bin/python3 examples/show_desktop_ui_tree_advanced.py
```

---

## Code Examples

### Basic AI Agent

```python
from open_alo_core import UnifiedRemoteDesktop, Point

with UnifiedRemoteDesktop() as remote:
    # ONE permission dialog
    remote.initialize(persist_mode=2, enable_capture=True)

    # Capture screen
    screenshot = remote.capture_screenshot()

    # Control input
    remote.type_text("Hello World!\n")
    remote.click(Point(500, 500))
```

### Window Management + Automation

```python
from open_alo_core import UnifiedRemoteDesktop, WindowManager, Point

# Find and activate window
wm = WindowManager()
editor = wm.find_window("TextEditor")
wm.activate(editor.id)

# Automate
with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)
    remote.type_text("Automated text input")
    remote.key_combo(["ctrl", "s"])  # Save
```

### Real-time AI Agent Loop

```python
from open_alo_core import UnifiedRemoteDesktop, Point

with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)

    while agent_running:
        # 1. Get current screen
        frame = remote.get_frame()

        # 2. AI decides action
        action = ai_model.process(frame)

        # 3. Execute
        if action['type'] == 'click':
            remote.click(Point(action['x'], action['y']))
        elif action['type'] == 'type':
            remote.type_text(action['text'])
```

---

## Requirements

- **OS:** Linux with Wayland (GNOME, KDE, etc.)
- **Python:** 3.10+
- **Dependencies:**
  - PyGObject (python3-gi)
  - GStreamer 1.0
  - PipeWire
  - XDG Desktop Portal

## Installation

```bash
cd open_alo_core
pip install -e .
```

## Documentation

- [Complete API Reference](../API_REFERENCE.md)
- [Quick Reference](../docs/UNIFIED_QUICK_REFERENCE.md)
- [Migration Guide](../docs/MIGRATION_TO_UNIFIED.md)
- [Implementation Details](../docs/UNIFIED_REMOTEDESKTOP_SUMMARY.md)

## Legacy Examples

Legacy examples using the old two-permission API have been moved to `archive/examples/`.

See `archive/README.md` for details and migration instructions.

---

## Common Patterns

### Pattern 1: Point Type
All examples use the Point NamedTuple:
```python
from open_alo_core import Point

# Instead of: controller.click(100, 200)
controller.click(Point(100, 200))  # Type-safe!
```

### Pattern 2: Context Managers
All examples use context managers:
```python
with UnifiedRemoteDesktop() as remote:
    # Auto-cleanup on exit
    remote.initialize(persist_mode=2, enable_capture=True)
```

---

## Prerequisites

### System Dependencies
```bash
# Ubuntu 25.10/Debian
sudo apt install \
    python3-gi \
    python3-gi-cairo \
    gstreamer1.0-pipewire \
    xdg-desktop-portal \
    xdg-desktop-portal-gnome
```

### Python Dependencies
```bash
cd open_alo_core
pip install -e .
```

---

## Tips

### First Run
- You'll see one permission dialog
- Check "Remember this decision" to make it persistent
- Run again and no dialogs will appear!

### Permissions
- `persist_mode=0` = Never persist (dialog every time)
- `persist_mode=1` = Persist while app running
- `persist_mode=2` = Persist until revoked (recommended)
- Delete token file to reset

### Testing
- All examples are safe to run
- Mouse movements are small and reversible
- No destructive operations

---

## Troubleshooting

### "No session_handle in response"
- Wait for the portal dialog to appear
- Click "Allow" when it shows up

### "ImportError: PyGObject required"
```bash
sudo apt install python3-gi python3-gi-cairo
```

### "Permission denied"
- You didn't check "Remember this decision"
- Run with `persist_mode=2` for persistence

---

## Next Steps

After running the examples:

1. **Build your own automation**
   - Start from `unified_minimal.py`
   - Add your own logic
2. **Integrate with AI agents**
   - Use `unified_ai_agent_demo.py` as template
3. **Contribute**
   - Fork the repo
   - Submit pull requests!

---

## See Also

- [Main README](../README.md) - Full documentation
- [API Reference](../API_REFERENCE.md) - Complete API docs

---

**Need help?** Check the troubleshooting section or open an issue!
