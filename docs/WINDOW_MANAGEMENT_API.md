# Window Management API Documentation

## Overview

The `open_alo_core.window_manager` module provides comprehensive window management for GNOME/Wayland via the Window Calls extension.

**Requirements:**
- GNOME Shell with Wayland
- [Window Calls Extension](https://extensions.gnome.org/extension/4724/window-calls/)

**Tested Environment:**
- Ubuntu 25.10 (Questing)
- Wayland + GNOME Shell / Unity
- Window Calls extension v13+

### Installing Window Calls Extension

**Option 1: GNOME Extensions Website**
```bash
# Visit https://extensions.gnome.org/extension/4724/window-calls/
# Click "Install" and follow browser prompts
```

**Option 2: Manual Installation**
```bash
# Install gnome-shell-extensions if needed
sudo apt install gnome-shell-extensions

# Enable the extension after installation
gnome-extensions enable window-calls@domandoman.github.com

# Verify it's enabled
gnome-extensions list --enabled | grep window-calls
```

**Verify Installation:**
```bash
# Check if D-Bus interface is available
gdbus introspect --session \
  --dest org.gnome.Shell \
  --object-path /org/gnome/Shell/Extensions/Windows

# Should show interface org.gnome.Shell.Extensions.Windows
```

## Quick Start

```python
from open_alo_core import WindowManager, activate_window

# Simple activation by name
activate_window("Text Editor")

# Or use the full API
wm = WindowManager()
windows = wm.list_windows()
editor = wm.find_window("Text Editor")
wm.activate(editor.id)
wm.maximize(editor.id)
```

## Complete D-Bus Methods from Window Calls Extension

### Available Methods (from gdbus introspect)

```
interface org.gnome.Shell.Extensions.Windows {
  methods:
    List(out s win);                                    # List all windows
    Details(in u winid, out s win);                     # Get detailed window info
    GetTitle(in u winid, out s win);                    # Get window title
    GetFrameRect(in u winid, out s frameRect);          # Get frame rectangle
    GetFrameBounds(in u winid, out s frameBounds);      # Get frame bounds
    MoveToWorkspace(in u winid, in u workspaceNum);     # Move to workspace
    MoveResize(in u winid, in i x, in i y,              # Move and resize
               in u width, in u height);
    Resize(in u winid, in u width, in u height);        # Resize window
    Move(in u winid, in i x, in i y);                   # Move window
    Maximize(in u winid);                               # Maximize window
    Minimize(in u winid);                               # Minimize window
    Unmaximize(in u winid);                             # Unmaximize window
    Unminimize(in u winid);                             # Unminimize/restore window
    Activate(in u winid);                               # Activate/focus window
    Close(in u winid);                                  # Close window
};
```

### Method Parameters
- `winid` (u): Window ID (unsigned integer)
- `x, y` (i): Coordinates (signed integer, can be negative)
- `width, height` (u): Dimensions (unsigned integer)
- `workspaceNum` (u): Workspace number (0-indexed)

## WindowManager Class

### Initialization

```python
wm = WindowManager(timeout=5)  # timeout in seconds for D-Bus calls
```

### Window Listing & Search

#### `list_windows(current_workspace_only=False) -> List[WindowInfo]`
List all open windows.

```python
# All windows
all_windows = wm.list_windows()

# Current workspace only
current_windows = wm.list_windows(current_workspace_only=True)
```

#### `find_window(query, match_title=True) -> Optional[WindowInfo]`
Find first window matching query.

```python
# Find by wm_class
editor = wm.find_window("gedit")

# Find by title
browser = wm.find_window("Google", match_title=True)

# wm_class only (faster)
terminal = wm.find_window("gnome-terminal", match_title=False)
```

#### `find_all_windows(query, match_title=True) -> List[WindowInfo]`
Find all windows matching query.

```python
# All terminal windows
terminals = wm.find_all_windows("terminal")
```

#### `get_focused_window() -> Optional[WindowInfo]`
Get currently focused window.

```python
focused = wm.get_focused_window()
if focused:
    print(f"Focused: {focused.wm_class}")
```

#### `get_details(window_id) -> Optional[Dict]`
Get detailed window information.

```python
details = wm.get_details(window_id)
# Returns: {
#   'wm_class', 'pid', 'id', 'width', 'height', 'x', 'y',
#   'maximized', 'focus', 'moveable', 'resizeable',
#   'canclose', 'canmaximize', 'canminimize', ...
# }
```

#### `get_title(window_id) -> Optional[str]`
Get window title by ID.

```python
title = wm.get_title(window_id)
```

### Window State Management

#### `activate(window_id) -> bool`
Activate (focus) a window.

```python
wm.activate(window_id)
```

#### `maximize(window_id) -> bool`
Maximize a window.

```python
wm.maximize(window_id)
```

#### `unmaximize(window_id) -> bool`
Unmaximize a window.

```python
wm.unmaximize(window_id)
```

#### `minimize(window_id) -> bool`
Minimize a window.

```python
wm.minimize(window_id)
```

#### `unminimize(window_id) -> bool`
Unminimize (restore) a window.

```python
wm.unminimize(window_id)
```

#### `close(window_id) -> bool`
Close a window.

```python
wm.close(window_id)
```

### Window Positioning

#### `move(window_id, x, y) -> bool`
Move window to position.

```python
# Move to top-left
wm.move(window_id, 0, 0)

# Negative coordinates supported
wm.move(window_id, -100, -50)
```

#### `resize(window_id, width, height) -> bool`
Resize window.

```python
wm.resize(window_id, 800, 600)
```

#### `move_resize(window_id, x, y, width, height) -> bool`
Move and resize in one operation (more efficient).

```python
wm.move_resize(window_id, 100, 100, 1920, 1080)
```

#### `get_frame_rect(window_id) -> Optional[Dict]`
Get window frame rectangle.

```python
frame = wm.get_frame_rect(window_id)
# Returns: {'x': 100, 'y': 50, 'width': 800, 'height': 600}
```

#### `get_frame_bounds(window_id) -> Optional[Dict]`
Get window frame bounds (may not work in GNOME 43+).

```python
bounds = wm.get_frame_bounds(window_id)
```

### Workspace Management

#### `move_to_workspace(window_id, workspace_num) -> bool`
Move window to different workspace.

```python
# Move to workspace 2 (0-indexed, so this is the 3rd workspace)
wm.move_to_workspace(window_id, 2)
```

## WindowInfo Dataclass

Represents window information:

```python
@dataclass
class WindowInfo:
    id: int                      # Window ID
    wm_class: str                # Application class
    wm_class_instance: str       # Class instance
    title: str                   # Window title
    pid: int                     # Process ID
    x: int                       # X position
    y: int                       # Y position
    width: int                   # Width
    height: int                  # Height
    workspace: int               # Workspace number
    monitor: int                 # Monitor number
    frame_type: int              # Frame type (0=normal)
    window_type: int             # Window type (0=normal)
    focus: bool                  # Is focused
    in_current_workspace: bool   # In current workspace
    maximized: int               # Maximized state
```

## Convenience Functions

Quick access functions without creating WindowManager instance:

```python
from open_alo_core import (
    list_windows,
    find_window,
    activate_window,
    get_focused_window
)

# List windows
windows = list_windows(current_workspace_only=True)

# Find window
editor = find_window("Text Editor")

# Activate by name or ID
activate_window("Text Editor")      # By name
activate_window(1290274482)         # By ID

# Get focused
focused = get_focused_window()
```

## Common Patterns

### Activate Application

```python
from open_alo_core import activate_window

# Simple way
activate_window("Text Editor")

# With error handling
from open_alo_core import WindowManager

wm = WindowManager()
window = wm.find_window("Text Editor")
if window:
    wm.activate(window.id)
else:
    print("Window not found")
```

### Position Window on Screen

```python
wm = WindowManager()
window = wm.find_window("Terminal")

# Move to top-left and resize
wm.move_resize(window.id, 0, 0, 1920, 1080)
```

### Tile Windows Side-by-Side

```python
wm = WindowManager()

# Get two windows
editor = wm.find_window("Text Editor")
browser = wm.find_window("Brave")

# Left half
wm.move_resize(editor.id, 0, 0, 960, 1080)

# Right half
wm.move_resize(browser.id, 960, 0, 960, 1080)
```

### Monitor Focused Window

```python
import time
from open_alo_core import get_focused_window

previous = None
while True:
    current = get_focused_window()
    if current and current.id != previous:
        print(f"Focus changed to: {current.wm_class}")
        previous = current.id
    time.sleep(0.5)
```

### List All Applications on Current Workspace

```python
wm = WindowManager()
windows = wm.list_windows(current_workspace_only=True)

print("Current workspace applications:")
for win in windows:
    if win.window_type == 0:  # Normal windows only
        print(f"  • {win.wm_class}: {win.title}")
```

## Error Handling

```python
from open_alo_core import WindowManager

try:
    wm = WindowManager()
    # Extension is available
except RuntimeError as e:
    print("Window Calls extension not installed")
    print("Install from: https://extensions.gnome.org/extension/4724/window-calls/")
```

## D-Bus Response Format

All D-Bus responses are automatically parsed. The raw format is:

```
List() → ('[{...}]',)
GetTitle() → ('Window Title',)
Details() → ('{...}',)
```

The WindowManager class handles all parsing automatically.

## Architecture

```
open_alo_core/
├── window_manager.py          # New comprehensive API
└── window.py                  # Legacy API (deprecated)

# Module structure
WindowManager              # Main class
├── _dbus_call()          # D-Bus communication
├── _parse_json_response() # Response parsing
├── list_windows()        # Window listing
├── find_window()         # Window search
├── activate()            # State management
├── move()                # Positioning
└── move_to_workspace()   # Workspace mgmt

# Convenience functions (module level)
├── list_windows()
├── find_window()
├── activate_window()
└── get_focused_window()
```

## Examples

See:
- [examples/focus_and_type.py](../examples/focus_and_type.py) - Window activation with typing
- [examples/window_management_demo.py](../examples/window_management_demo.py) - Complete demo

## Notes

- All coordinates can be negative for off-screen positioning
- Window IDs are persistent during the window's lifetime
- Some methods may fail if window doesn't support the operation (check `details['can*']`)
- The extension must be enabled in GNOME Shell
- Works on Wayland and X11 (GNOME Shell only)
