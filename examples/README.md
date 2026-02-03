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

Legacy examples using the old two-permission API have been moved to `archive/examples/`:
- `agent_example.py`
- `persistent_session_example.py`
- `click_automation.py`
- `keyboard_shortcuts.py`
- `screenshot_automation.py`
- `workflow_automation.py`
- `focus_and_type.py`
- `api_server.py`

See `archive/README.md` for details and migration instructions.

**NEW!** Automates clicking at specific screen coordinates with CLI options:

```bash
# Single click
/usr/bin/python3 examples/click_automation.py --x 500 --y 500

# Triple click with delay
/usr/bin/python3 examples/click_automation.py --x 500 --y 500 --clicks 3 --delay 0.5

# Right-click
/usr/bin/python3 examples/click_automation.py --x 960 --y 540 --button right

# Dry run (see what would happen)
/usr/bin/python3 examples/click_automation.py --x 100 --y 100 --dry-run
```

### 4. screenshot_automation.py 📸 SCREENSHOT AUTOMATION

**NEW!** Automates taking screenshots with various options:

```bash
# Single screenshot
/usr/bin/python3 examples/screenshot_automation.py -o screenshot.png

# Multiple screenshots with delay
/usr/bin/python3 examples/screenshot_automation.py -o series.png --count 10 --delay 5

# Timelapse with timestamps
/usr/bin/python3 examples/screenshot_automation.py -o timelapse.png --count 60 --delay 60 --timestamp

# Dry run
/usr/bin/python3 examples/screenshot_automation.py -o test.png --dry-run
```

### 5. keyboard_shortcuts.py ⌨️ KEYBOARD AUTOMATION

**NEW!** Automates keyboard shortcuts and text input:

```bash
# Type text
/usr/bin/python3 examples/keyboard_shortcuts.py --type "Hello World"

# Press single key
/usr/bin/python3 examples/keyboard_shortcuts.py --key Return

# Key combination (Ctrl+C)
/usr/bin/python3 examples/keyboard_shortcuts.py --combo Control c

# Use preset shortcut
/usr/bin/python3 examples/keyboard_shortcuts.py --preset save
/usr/bin/python3 examples/keyboard_shortcuts.py --preset copy
/usr/bin/python3 examples/keyboard_shortcuts.py --preset paste

# Type with custom delay
/usr/bin/python3 examples/keyboard_shortcuts.py --type "Slow" --char-delay 0.2
```

### 6. workflow_automation.py 🔄 COMPLETE WORKFLOWS

**NEW!** Combines multiple operations in a single workflow:

```bash
# Screenshot → Click → Type → Screenshot
/usr/bin/python3 examples/workflow_automation.py \
    --click-x 500 --click-y 500 \
    --type "Hello World" \
    --output result.png

# Full workflow with before/after comparison
/usr/bin/python3 examples/workflow_automation.py \
    --click-x 500 --click-y 500 \
    --type "Test input" \
    --shortcut save \
    --before-screenshot before.png \
    --output after.png

# Just take screenshots
/usr/bin/python3 examples/workflow_automation.py \
    --output screenshot.png \
    --no-click
```

### 7. api_server.py 🌐 HTTP API

REST API server using the clean API:

```bash
# Start server
/usr/bin/python3 examples/api_server.py

# Then test with curl:
curl http://localhost:8080/status
curl -X POST http://localhost:8080/screenshot
curl -X POST -d '{"x": 100, "y": 200}' http://localhost:8080/click
```

---

## Quick Start Guide

### Step 1: Test Basic Functionality
```bash
# Basic agent example
/usr/bin/python3 examples/agent_example.py
```

### Step 2: Try Session Persistence
```bash
# Run twice to see persistence in action
/usr/bin/python3 examples/persistent_session_example.py
/usr/bin/python3 examples/persistent_session_example.py
```

### Step 3: Automate Specific Tasks
```bash
# Click automation
/usr/bin/python3 examples/click_automation.py --x 500 --y 500 --clicks 3

# Screenshot automation
/usr/bin/python3 examples/screenshot_automation.py -o test.png

# Keyboard shortcuts
/usr/bin/python3 examples/keyboard_shortcuts.py --preset copy
```

### Step 4: Create Workflows
```bash
# Complete workflow
/usr/bin/python3 examples/workflow_automation.py \
    --click-x 500 --click-y 500 \
    --type "Automated input" \
    --shortcut save \
    --output result.png
```

---

## Example Comparison

| Example                       | Purpose             | Complexity | Use Case                    |
| ----------------------------- | ------------------- | ---------- | --------------------------- |
| agent_example.py              | Demo all features   | Medium     | Getting started             |
| persistent_session_example.py | Session persistence | Low        | Understanding persist_mode  |
| click_automation.py           | Mouse clicks        | Low        | UI testing, automation      |
| screenshot_automation.py      | Screenshots         | Low        | Monitoring, documentation   |
| keyboard_shortcuts.py         | Keyboard input      | Low        | Macros, shortcuts           |
| workflow_automation.py        | Combined operations | Medium     | Complex workflows           |
| api_server.py                 | HTTP API            | High       | Integration, remote control |

---

## Common Patterns

### Pattern 1: Error Handling
All examples follow this pattern:
```python
from open_alo_core import WaylandInput, PermissionDenied, CoreError

try:
    with WaylandInput() as controller:
        controller.initialize(persist_mode=2)
        # Do work
except PermissionDenied:
    print("User denied permission")
except CoreError as e:
    print(f"Error: {e}")
```

### Pattern 2: Point Type
All examples use the Point NamedTuple:
```python
from open_alo_core import Point

# Instead of: controller.click(100, 200)
controller.click(Point(100, 200))  # Type-safe!
```

### Pattern 3: Context Managers
All examples use context managers:
```python
with WaylandInput() as controller:
    # Auto-cleanup on exit
    controller.initialize(persist_mode=2)
```

### Pattern 4: Command-Line Arguments
Advanced examples use argparse:
```python
parser = argparse.ArgumentParser()
parser.add_argument('--x', type=int, required=True)
args = parser.parse_args()
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
- You'll see permission dialogs
- Check "Remember this decision" to make them persistent
- Run again and no dialogs will appear!

### Screenshots
- When the dialog appears, select your **MONITOR/SCREEN**
- Not the webcam thumbnail!
- The example will warn you if you selected the webcam

### Permissions
- `persist_mode=0` = Never persist (dialog every time)
- `persist_mode=1` = Persist while app running
- `persist_mode=2` = Persist until revoked (recommended)
- Delete `~/.config/open_alo_core/tokens.json` to reset

### Testing
- All examples are safe to run
- Mouse movements are small and reversible
- No destructive operations
- Use `--dry-run` flag where available to preview actions

---

## Troubleshooting

### "No session_handle in response"
- Wait for the portal dialog to appear
- Click "Allow" when it shows up

### "ImportError: PyGObject required"
```bash
sudo apt install python3-gi python3-gi-cairo
```

### "Screenshot captures webcam"
- In the dialog, select the big rectangle (monitor)
- Not the small webcam thumbnail
- The example will warn you: "📷 Webcam detected!"

### "Permission denied"
- You didn't check "Remember this decision"
- Delete token file and try again
- Run with `persist_mode=2` for persistence

---

## Next Steps

After running the examples:

1. **Build your own automation**
   - Copy patterns from click_automation.py or keyboard_shortcuts.py
   - Customize for your use case
   - Add argparse for CLI options

2. **Create workflows**
   - Use workflow_automation.py as a template
   - Combine multiple operations
   - Add before/after screenshots

3. **Integrate with other tools**
   - Use api_server.py for remote control
   - Combine with cron for scheduled tasks
   - Integrate with CI/CD pipelines

4. **Contribute**
   - Fork the repo
   - Add new examples
   - Submit pull requests!

---

## See Also

- [Main README](../README.md) - Full documentation
- [API Documentation](../API.md) - API reference
- [CHANGELOG](../CHANGELOG.md) - Version history

---

**Need help?** Check the troubleshooting section or open an issue!
