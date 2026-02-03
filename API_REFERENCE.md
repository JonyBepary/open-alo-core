# open_alo_core API Reference

**Version:** 0.1.0
**Platform:** Linux (Wayland/X11)
**License:** MIT

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Classes](#core-classes)
  - [UnifiedRemoteDesktop](#unifiedremotedesktop) ⭐ **RECOMMENDED for AI Agents**
  - [WaylandInput](#waylandinput) (Legacy)
  - [WaylandCapture](#waylandcapture) (Legacy)
  - [WindowManager](#windowmanager)
- [Types](#types)
  - [Point](#point)
  - [Size](#size)
  - [Rect](#rect)
  - [WindowInfo](#windowinfo)
  - [WindowType](#windowtype)
  - [FrameType](#frametype)
- [Exceptions](#exceptions)
- [Utilities](#utilities)
- [Constants](#constants)
- [Complete API Index](#complete-api-index)

---

## Overview

`open_alo_core` is a standalone desktop automation SDK for Linux that provides:

- **Input Control**: Mouse and keyboard control via XDG RemoteDesktop Portal
- **Screen Capture**: Native Wayland screenshot via PipeWire and XDG ScreenCast Portal
- **Window Management**: Comprehensive window control via GNOME Shell D-Bus (requires Window Calls extension)
- **Zero Dependencies on AI/ML**: Pure hardware abstraction layer
- **Wayland Native**: No X11 fallback, works on modern Wayland compositors

### Architecture

```
open_alo_core/
├── wayland/
│   ├── input.py          # WaylandInput - Mouse & keyboard control
│   └── capture.py        # WaylandCapture - Screen capture
├── window_manager.py     # WindowManager - Window management
├── types.py              # Data types (Point, Size, Rect)
├── exceptions.py         # Exception hierarchy
└── utils/                # Utility functions
```

### System Requirements

- **OS**: Linux with Wayland compositor (GNOME Shell, KDE Plasma, Sway, etc.)
- **Python**: 3.10+
- **Dependencies**:
  - PyGObject (python3-gi)
  - GStreamer 1.0 (for capture)
  - PipeWire (for capture)
- **Window Management** (GNOME only):
  - [Window Calls Extension](https://extensions.gnome.org/extension/4724/window-calls/)
  - Install and enable: `gnome-extensions enable window-calls@domandoman.github.com`

**Tested Environment:**
- Ubuntu 25.10 (Questing), Wayland + GNOME/Unity
- Window Calls extension v13+

---

## Installation

```bash
# Install from source
cd open_alo_core
pip install -e .

# Or install dependencies manually
sudo apt install python3-gi gstreamer1.0-tools pipewire
```

---

## Quick Start

### Unified Approach (Recommended for AI Agents) ⭐

```python
from open_alo_core import UnifiedRemoteDesktop, Point

# ONE permission dialog for both input and capture
with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)

    # Screen capture
    screenshot = remote.capture_screenshot()  # PNG bytes
    frame = remote.get_frame()                # Real-time stream
    width, height = remote.get_screen_size()

    # Input control
    remote.click(Point(500, 500))
    remote.type_text("Hello World!")
    remote.key_combo(["ctrl", "c"])
```

### Legacy Approach (Separate Input/Capture)

```python
from open_alo_core import WaylandInput, Point

# Context manager automatically cleans up
with WaylandInput() as ctrl:
    # Initialize with persistent permissions (approve once)
    ctrl.initialize(persist_mode=2)

    # Click at coordinates
    ctrl.click(Point(500, 500))

    # Type text
    ctrl.type_text("Hello World!")

    # Press keys
    ctrl.press_key("Return")

    # Keyboard shortcuts
    ctrl.key_combo(["Control", "a"])  # Select all
    ctrl.key_combo(["Control", "c"])  # Copy
```

### Screen Capture

```python
from open_alo_core import WaylandCapture
from pathlib import Path

with WaylandCapture() as capture:
    # User will be prompted to select screen/window
    result = capture.capture_screen()

    # Save as PNG
    Path("/tmp/screenshot.png").write_bytes(result.data)

    print(f"Captured {result.source_type}: {result.size}")
```

### Window Management

```python
from open_alo_core import WindowManager, activate_window

# Simple activation
activate_window("Text Editor")

# Full API
wm = WindowManager()
windows = wm.list_windows()
editor = wm.find_window("Text Editor")

if editor:
    wm.activate(editor.id)
    wm.maximize(editor.id)
    wm.move_resize(editor.id, 0, 0, 1920, 1080)
```

---

## Core Classes

### UnifiedRemoteDesktop ⭐

**Full path**: `open_alo_core.wayland.unified.UnifiedRemoteDesktop`

**RECOMMENDED for AI Agents** - Provides both input control and screen capture with a single permission dialog.

#### Why Use UnifiedRemoteDesktop?

- ✅ **ONE permission dialog** (vs two separate dialogs)
- ✅ **Simpler code** (single class vs WaylandInput + WaylandCapture)
- ✅ **Better UX** (same approach as RustDesk, Chrome Remote Desktop)
- ✅ **AI-ready** (real-time screen streaming + input control)

#### Constructor

```python
UnifiedRemoteDesktop(token_path: Optional[Path] = None)
```

**Parameters:**
- `token_path` (Optional[Path]): Custom path for storing permission tokens. Defaults to `~/.config/open_alo_core/unified_token.json`

#### Methods

##### `initialize(persist_mode: int = 2, enable_capture: bool = True) -> bool`

Initialize remote desktop session with a single permission dialog for both input and capture.

**Parameters:**
- `persist_mode` (int): Permission persistence behavior
  - `0` = Transient (request permission each time)
  - `1` = Session (persist until application terminates)
  - `2` = Persistent (persist until explicitly revoked; recommended)
- `enable_capture` (bool): Enable screen capture capabilities (required for AI agents)

**Returns:**
- `bool`: True if initialization succeeded

**Raises:**
- `PermissionDenied`: User denied permission
- `SessionError`: Portal communication failed

**Example:**
```python
with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)
    # Ready to use!
```

##### `capture_screenshot() -> bytes`

Capture current screen as PNG image.

**Returns:**
- `bytes`: PNG image data

**Example:**
```python
screenshot = remote.capture_screenshot()
Path("/tmp/screenshot.png").write_bytes(screenshot)
```

##### `get_frame() -> bytes`

Get real-time frame from video stream (for continuous monitoring).

**Returns:**
- `bytes`: PNG image data

**Example:**
```python
while agent_running:
    frame = remote.get_frame()
    action = ai_model.decide(frame)
    # Execute action...
```

##### `get_screen_size() -> Tuple[int, int]`

Get screen resolution.

**Returns:**
- `Tuple[int, int]`: (width, height) in pixels

**Example:**
```python
width, height = remote.get_screen_size()
center = Point(width // 2, height // 2)
```

##### `click(point: Point, button: int = 1) -> None`

Click mouse at specific coordinates.

**Parameters:**
- `point` (Point): Click coordinates
- `button` (int): Mouse button (1=left, 2=middle, 3=right)

**Example:**
```python
remote.click(Point(100, 200))           # Left click
remote.click(Point(100, 200), button=3) # Right click
```

##### `move_mouse(point: Point) -> None`

Move mouse cursor to coordinates.

**Parameters:**
- `point` (Point): Target coordinates

**Example:**
```python
remote.move_mouse(Point(500, 500))
```

##### `type_text(text: str, interval: float = 0.05) -> None`

Type text with optional delay between characters.

**Parameters:**
- `text` (str): Text to type
- `interval` (float): Delay between characters in seconds

**Example:**
```python
remote.type_text("Hello World!\n")
remote.type_text("fast typing", interval=0.01)
```

##### `press_key(key: Union[str, int]) -> None`

Press and release a single key.

**Parameters:**
- `key` (Union[str, int]): Key name or code

**Example:**
```python
remote.press_key("enter")
remote.press_key("escape")
remote.press_key("f5")
```

##### `key_combo(keys: List[Union[str, int]]) -> None`

Press keyboard shortcut (hold all keys, then release).

**Parameters:**
- `keys` (List[Union[str, int]]): List of keys to press together

**Example:**
```python
remote.key_combo(["ctrl", "c"])         # Copy
remote.key_combo(["ctrl", "shift", "t"]) # New terminal tab
remote.key_combo(["alt", "f4"])         # Close window
```

##### `close() -> None`

Release resources and close session. Called automatically when using context manager.

**Example:**
```python
# Manual cleanup
remote = UnifiedRemoteDesktop()
remote.initialize()
# ... use remote ...
remote.close()

# Auto cleanup (recommended)
with UnifiedRemoteDesktop() as remote:
    remote.initialize()
    # ... use remote ...
# Automatically closed
```

#### Complete Example

```python
from open_alo_core import UnifiedRemoteDesktop, WindowManager, Point
from pathlib import Path

# Setup window
wm = WindowManager()
app = wm.find_window("TextEditor")
wm.activate(app.id)

# AI agent loop
with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)

    while True:
        # 1. Capture screen
        frame = remote.get_frame()

        # 2. AI decides action
        action = ai_model.process(frame)

        # 3. Execute
        if action['type'] == 'click':
            remote.click(Point(action['x'], action['y']))
        elif action['type'] == 'type':
            remote.type_text(action['text'])
        elif action['type'] == 'screenshot':
            screenshot = remote.capture_screenshot()
            Path(f"capture_{time.time()}.png").write_bytes(screenshot)
```

---

### WaylandInput (Legacy)

**Full path**: `open_alo_core.wayland.input.WaylandInput`

> **Note:** For new projects, prefer `UnifiedRemoteDesktop` which combines input and capture in one permission dialog.

Provides mouse and keyboard control on Wayland using XDG RemoteDesktop Portal.

#### Constructor

```python
WaylandInput(token_path: Optional[Path] = None)
```

**Parameters:**
- `token_path` (Optional[Path]): Custom path for storing permission tokens. If `None`, uses `~/.config/open_alo_core/tokens.json`

**Example:**
```python
# Default token location
ctrl = WaylandInput()

# Custom token location
ctrl = WaylandInput(token_path=Path("/tmp/tokens.json"))

# Ephemeral session (no persistence)
ctrl = WaylandInput()
ctrl.initialize(persist_mode=0)
```

#### Methods

##### `initialize(persist_mode: int = 0) -> None`

Initialize portal session and request input permissions.

**Parameters:**
- `persist_mode` (int): Permission persistence behavior
  - `0` = Transient (request permission each time)
  - `1` = Session (persist until application terminates)
  - `2` = Persistent (persist until explicitly revoked; recommended)

**Raises:**
- `PermissionDenied`: User denied permission
- `SessionError`: Session creation failed
- `RuntimeError`: Not running on Wayland

**Example:**
```python
ctrl = WaylandInput()
ctrl.initialize(persist_mode=2)  # Approve once, persist forever
```

##### `click(point: Point, button: int = 1) -> None`

Click at screen coordinates.

**Parameters:**
- `point` (Point): Screen coordinates (x, y)
- `button` (int): Mouse button
  - `1`: Left button (default)
  - `2`: Middle button
  - `3`: Right button

**Raises:**
- `RuntimeError`: Not initialized
- `InputError`: Click failed

**Example:**
```python
# Left click
ctrl.click(Point(500, 500))

# Right click
ctrl.click(Point(100, 100), button=3)

# Middle click
ctrl.click(Point(200, 200), button=2)
```

##### `move_mouse(point: Point) -> None`

Move mouse cursor to coordinates.

**Parameters:**
- `point` (Point): Target coordinates

**Raises:**
- `RuntimeError`: Not initialized
- `InputError`: Move failed

**Example:**
```python
ctrl.move_mouse(Point(800, 600))
```

##### `type_text(text: str, interval: float = 0.01) -> None`

Type a text string character by character.

**Parameters:**
- `text` (str): Unicode text to type
- `interval` (float): Delay between characters in seconds (default: 0.01)

**Raises:**
- `RuntimeError`: Not initialized
- `InputError`: Typing failed

**Example:**
```python
# Normal typing
ctrl.type_text("Hello World!")

# Fast typing
ctrl.type_text("Speed typing", interval=0.001)

# Unicode support
ctrl.type_text("你好世界 🌍")
```

##### `press_key(key: str) -> None`

Press and release a single key.

**Parameters:**
- `key` (str): Key name (e.g., "Return", "Escape", "a"). See [Key Names](#key-names) for full list.

**Raises:**
- `RuntimeError`: Not initialized
- `InputError`: Key press failed

**Example:**
```python
ctrl.press_key("Return")     # Enter
ctrl.press_key("Escape")     # Esc
ctrl.press_key("Tab")        # Tab
ctrl.press_key("space")      # Spacebar
ctrl.press_key("a")          # Letter 'a'
```

##### `key_combo(keys: List[str]) -> None`

Press multiple keys together (keyboard shortcut).

**Parameters:**
- `keys` (List[str]): List of keys to press together

**Raises:**
- `RuntimeError`: Not initialized
- `InputError`: Key combo failed

**Example:**
```python
# Common shortcuts
ctrl.key_combo(["Control", "a"])      # Select all
ctrl.key_combo(["Control", "c"])      # Copy
ctrl.key_combo(["Control", "v"])      # Paste
ctrl.key_combo(["Control", "Shift", "t"])  # Reopen tab
ctrl.key_combo(["Alt", "Tab"])        # Switch window
ctrl.key_combo(["Super", "d"])        # Show desktop
```

##### `close() -> None`

Release resources and close portal session.

**Example:**
```python
ctrl = WaylandInput()
ctrl.initialize(persist_mode=2)
# ... use controller ...
ctrl.close()  # Clean up

# Or use context manager (auto cleanup)
with WaylandInput() as ctrl:
    ctrl.initialize(persist_mode=2)
    # ... automatically closed
```

#### Key Names

The following key names are supported (case-insensitive aliases normalized automatically):

**Special Keys:**
- `Return`, `Enter` → Enter key
- `Escape`, `Esc` → Escape
- `Tab` → Tab
- `space` → Spacebar
- `BackSpace` → Backspace
- `Delete`, `Del` → Delete

**Navigation:**
- `Home`, `End`
- `Page_Up`, `PageUp`
- `Page_Down`, `PageDown`
- `Left`, `Right`, `Up`, `Down` → Arrow keys

**Modifiers:**
- `Control`, `Ctrl` → Control key
- `Alt` → Alt key
- `Shift` → Shift key
- `Super`, `Win`, `Cmd`, `Command` → Super/Windows/Command key

**Function Keys:**
- `F1` through `F12`

**Characters:**
- Any letter: `a`, `b`, `c`, ..., `z`
- Any number: `0`, `1`, `2`, ..., `9`
- Symbols: `-`, `=`, `[`, `]`, `;`, `'`, etc.

---

### WaylandCapture (Legacy)

**Full path**: `open_alo_core.wayland.capture.WaylandCapture`

> **Note:** For new projects, prefer `UnifiedRemoteDesktop` which combines input and capture in one permission dialog.

Provides screen capture on Wayland using PipeWire and XDG ScreenCast Portal.

#### Constructor

```python
WaylandCapture()
```

No parameters needed.

**Example:**
```python
capture = WaylandCapture()

# Or use context manager
with WaylandCapture() as capture:
    result = capture.capture_screen()
```

#### Methods

##### `capture_screen() -> CaptureResult`

Capture the screen with user selection.

Shows a permission dialog asking the user which screen/window to capture. Returns PNG image data.

**Returns:**
- `CaptureResult`: Object containing:
  - `data` (bytes): PNG image data
  - `source_type` (str): Source type ("monitor", "window", "camera")
  - `size` (Tuple[int, int]): Image dimensions (width, height)

**Raises:**
- `CaptureError`: Capture failed
- `PermissionDenied`: User denied permission

**Example:**
```python
with WaylandCapture() as capture:
    # User selects screen/window
    result = capture.capture_screen()

    # Save to file
    from pathlib import Path
    Path("/tmp/screenshot.png").write_bytes(result.data)

    # Get info
    print(f"Captured {result.source_type}")
    print(f"Size: {result.size[0]}x{result.size[1]}")
    print(f"Data: {len(result.data)} bytes")
```

##### `close() -> None`

Release resources and close session.

**Example:**
```python
capture = WaylandCapture()
result = capture.capture_screen()
capture.close()

# Or use context manager
with WaylandCapture() as capture:
    result = capture.capture_screen()
    # Automatically closed
```

#### CaptureResult

Result object returned by `capture_screen()`.

**Attributes:**
- `data` (bytes): PNG image data (ready to save or process)
- `source_type` (str): Type of source captured
  - `"monitor"`: Full screen capture
  - `"window"`: Single window capture
  - `"camera"`: Camera capture (rare)
- `size` (Tuple[int, int]): Image dimensions as (width, height)

**Example:**
```python
result = capture.capture_screen()

# Save to file
with open("/tmp/shot.png", "wb") as f:
    f.write(result.data)

# Load with PIL
from PIL import Image
from io import BytesIO
img = Image.open(BytesIO(result.data))

# Get dimensions
width, height = result.size
```

---

### WindowManager

**Full path**: `open_alo_core.window_manager.WindowManager`

Comprehensive window management for GNOME Shell via D-Bus.

**Requirements:**
- GNOME Shell with Wayland or X11
- [Window Calls Extension](https://extensions.gnome.org/extension/4724/window-calls/) installed and enabled

#### Constructor

```python
WindowManager(timeout: int = 5)
```

**Parameters:**
- `timeout` (int): Default timeout for D-Bus calls in seconds (default: 5)

**Raises:**
- `RuntimeError`: Window Calls extension not available

**Example:**
```python
wm = WindowManager()  # Default 5s timeout
wm = WindowManager(timeout=10)  # Custom timeout
```

#### Window Listing & Search Methods

##### `list_windows(current_workspace_only: bool = False) -> List[WindowInfo]`

List all open windows.

**Parameters:**
- `current_workspace_only` (bool): Only return windows in current workspace (default: False)

**Returns:**
- `List[WindowInfo]`: List of window information objects

**Example:**
```python
# All windows
all_windows = wm.list_windows()
for win in all_windows:
    print(f"{win.wm_class}: {win.title}")

# Current workspace only
current = wm.list_windows(current_workspace_only=True)
print(f"Windows on current workspace: {len(current)}")
```

##### `find_window(query: str, match_title: bool = True) -> Optional[WindowInfo]`

Find first window matching query.

**Parameters:**
- `query` (str): Search string (case-insensitive)
- `match_title` (bool): Also search in window titles (default: True)

**Returns:**
- `WindowInfo`: First matching window, or `None` if not found

**Example:**
```python
# Find by wm_class (fast)
editor = wm.find_window("gedit")

# Find by title
browser = wm.find_window("Google Chrome", match_title=True)

# wm_class only (faster, skips title search)
terminal = wm.find_window("gnome-terminal", match_title=False)

# Case-insensitive
vscode = wm.find_window("CODE")  # Finds "code"
```

##### `find_all_windows(query: str, match_title: bool = True) -> List[WindowInfo]`

Find all windows matching query.

**Parameters:**
- `query` (str): Search string (case-insensitive)
- `match_title` (bool): Also search in window titles (default: True)

**Returns:**
- `List[WindowInfo]`: All matching windows

**Example:**
```python
# Find all terminal windows
terminals = wm.find_all_windows("terminal")
print(f"Found {len(terminals)} terminal windows")

# Find all browser windows
browsers = wm.find_all_windows("browser")
```

##### `get_focused_window() -> Optional[WindowInfo]`

Get currently focused window.

**Returns:**
- `WindowInfo`: Focused window, or `None` if none

**Example:**
```python
focused = wm.get_focused_window()
if focused:
    print(f"Currently focused: {focused.wm_class}")
    print(f"Title: {focused.title}")
else:
    print("No window focused")
```

##### `get_details(window_id: int) -> Optional[Dict]`

Get detailed information about a window.

**Parameters:**
- `window_id` (int): Window ID

**Returns:**
- `Dict`: Dictionary with detailed properties, or `None` if failed

**Properties returned:**
- `wm_class`, `wm_class_instance`, `pid`, `id`
- `x`, `y`, `width`, `height`
- `maximized`, `focus`, `in_current_workspace`
- `moveable`, `resizeable`, `canclose`, `canmaximize`, `canminimize`, `canshade`
- `frame_type`, `window_type`, `layer`, `monitor`
- `role`, `display`, `area`, `area_all`, `area_cust`

**Example:**
```python
details = wm.get_details(window_id)
if details:
    print(f"Maximized: {details['maximized']}")
    print(f"Can maximize: {details['canmaximize']}")
    print(f"Moveable: {details['moveable']}")
```

##### `get_title(window_id: int) -> Optional[str]`

Get window title by ID.

**Parameters:**
- `window_id` (int): Window ID

**Returns:**
- `str`: Window title, or `None` if failed

**Example:**
```python
title = wm.get_title(window_id)
print(f"Window title: {title}")
```

#### Window State Management Methods

##### `activate(window_id: int) -> bool`

Activate (focus) a window.

**Parameters:**
- `window_id` (int): Window ID

**Returns:**
- `bool`: True if successful

**Example:**
```python
editor = wm.find_window("Text Editor")
if editor:
    wm.activate(editor.id)
```

##### `maximize(window_id: int) -> bool`

Maximize a window.

**Parameters:**
- `window_id` (int): Window ID

**Returns:**
- `bool`: True if successful

**Example:**
```python
wm.maximize(window_id)
```

##### `unmaximize(window_id: int) -> bool`

Unmaximize (restore) a window.

**Parameters:**
- `window_id` (int): Window ID

**Returns:**
- `bool`: True if successful

**Example:**
```python
wm.unmaximize(window_id)
```

##### `minimize(window_id: int) -> bool`

Minimize a window.

**Parameters:**
- `window_id` (int): Window ID

**Returns:**
- `bool`: True if successful

**Example:**
```python
wm.minimize(window_id)
```

##### `unminimize(window_id: int) -> bool`

Unminimize (restore) a window.

**Parameters:**
- `window_id` (int): Window ID

**Returns:**
- `bool`: True if successful

**Example:**
```python
wm.unminimize(window_id)
```

##### `close(window_id: int) -> bool`

Close a window.

**Parameters:**
- `window_id` (int): Window ID

**Returns:**
- `bool`: True if successful

**Example:**
```python
# Close a window
if wm.close(window_id):
    print("Window closed")
```

#### Window Positioning Methods

##### `move(window_id: int, x: int, y: int) -> bool`

Move window to position.

**Parameters:**
- `window_id` (int): Window ID
- `x` (int): X coordinate (can be negative)
- `y` (int): Y coordinate (can be negative)

**Returns:**
- `bool`: True if successful

**Example:**
```python
# Move to top-left
wm.move(window_id, 0, 0)

# Negative coordinates supported (off-screen)
wm.move(window_id, -100, -50)
```

##### `resize(window_id: int, width: int, height: int) -> bool`

Resize window.

**Parameters:**
- `window_id` (int): Window ID
- `width` (int): New width in pixels
- `height` (int): New height in pixels

**Returns:**
- `bool`: True if successful

**Example:**
```python
# Standard HD resolution
wm.resize(window_id, 1920, 1080)

# Custom size
wm.resize(window_id, 800, 600)
```

##### `move_resize(window_id: int, x: int, y: int, width: int, height: int) -> bool`

Move and resize window in one operation (more efficient).

**Parameters:**
- `window_id` (int): Window ID
- `x` (int): X coordinate
- `y` (int): Y coordinate
- `width` (int): Width in pixels
- `height` (int): Height in pixels

**Returns:**
- `bool`: True if successful

**Example:**
```python
# Position at (100, 100) with size 1920x1080
wm.move_resize(window_id, 100, 100, 1920, 1080)

# Tile left half of 1920x1080 screen
wm.move_resize(window_id, 0, 0, 960, 1080)
```

##### `get_frame_rect(window_id: int) -> Optional[Dict]`

Get window frame rectangle.

**Parameters:**
- `window_id` (int): Window ID

**Returns:**
- `Dict`: Dictionary with `x`, `y`, `width`, `height`, or `None` if failed

**Example:**
```python
frame = wm.get_frame_rect(window_id)
if frame:
    print(f"Position: ({frame['x']}, {frame['y']})")
    print(f"Size: {frame['width']}x{frame['height']}")
```

##### `get_frame_bounds(window_id: int) -> Optional[Dict]`

Get window frame bounds (may not work in GNOME 43+).

**Parameters:**
- `window_id` (int): Window ID

**Returns:**
- `Dict`: Frame bounds dictionary, or `None` if failed

**Example:**
```python
bounds = wm.get_frame_bounds(window_id)
```

#### Workspace Management Methods

##### `move_to_workspace(window_id: int, workspace_num: int) -> bool`

Move window to different workspace.

**Parameters:**
- `window_id` (int): Window ID
- `workspace_num` (int): Target workspace number (0-indexed)

**Returns:**
- `bool`: True if successful

**Example:**
```python
# Move to workspace 0 (first workspace)
wm.move_to_workspace(window_id, 0)

# Move to workspace 2 (third workspace)
wm.move_to_workspace(window_id, 2)
```

---

## Types

### Point

**Full path**: `open_alo_core.types.Point`

2D screen coordinates.

**Definition:**
```python
class Point(NamedTuple):
    x: int
    y: int
```

**Example:**
```python
from open_alo_core import Point

# Create point
p = Point(500, 500)
print(p.x, p.y)  # 500 500

# Use in click
ctrl.click(Point(100, 200))

# Immutable
p = Point(10, 20)
# p.x = 30  # Error: cannot modify NamedTuple
```

---

### Size

**Full path**: `open_alo_core.types.Size`

Width and height dimensions.

**Definition:**
```python
class Size(NamedTuple):
    width: int
    height: int
```

**Example:**
```python
from open_alo_core import Size

size = Size(1920, 1080)
print(f"{size.width}x{size.height}")  # 1920x1080
```

---

### Rect

**Full path**: `open_alo_core.types.Rect`

Rectangle with position and size.

**Definition:**
```python
class Rect(NamedTuple):
    x: int
    y: int
    width: int
    height: int
```

**Properties:**
- `center` → Point: Center point of rectangle
- `top_left` → Point: Top-left corner
- `bottom_right` → Point: Bottom-right corner

**Methods:**
- `contains(point: Point) -> bool`: Check if point is inside rectangle

**Example:**
```python
from open_alo_core import Rect, Point

rect = Rect(100, 100, 800, 600)

# Get center
center = rect.center  # Point(500, 400)

# Get corners
top_left = rect.top_left  # Point(100, 100)
bottom_right = rect.bottom_right  # Point(900, 700)

# Check if point inside
point = Point(500, 400)
if rect.contains(point):
    print("Point is inside rectangle")
```

---

### WindowInfo

**Full path**: `open_alo_core.window_manager.WindowInfo`

Window information container (dataclass).

**Attributes:**
- `id` (int): Window ID (unique during window lifetime)
- `wm_class` (str): Application class (e.g., "org.gnome.Nautilus")
- `wm_class_instance` (str): Class instance
- `title` (str): Window title
- `pid` (int): Process ID
- `x` (int): X position
- `y` (int): Y position
- `width` (int): Width in pixels
- `height` (int): Height in pixels
- `workspace` (int): Workspace number (0-indexed)
- `monitor` (int): Monitor number
- `frame_type` (int): Frame type (0=normal, 1=frameless)
- `window_type` (int): Window type (0=normal, 1=desktop, 2=dock, etc.)
- `focus` (bool): Currently focused
- `in_current_workspace` (bool): In current workspace
- `maximized` (int): Maximized state

**Example:**
```python
windows = wm.list_windows()
for win in windows:
    print(f"ID: {win.id}")
    print(f"Class: {win.wm_class}")
    print(f"Title: {win.title}")
    print(f"Position: ({win.x}, {win.y})")
    print(f"Size: {win.width}x{win.height}")
    print(f"Focused: {win.focus}")
    print(f"Workspace: {win.workspace}")
```

---

### WindowType

**Full path**: `open_alo_core.window_manager.WindowType`

Window type enumeration.

**Values:**
- `NORMAL = 0`: Normal application window
- `DESKTOP = 1`: Desktop window
- `DOCK = 2`: Dock/panel window
- `DIALOG = 3`: Dialog window
- `MODAL_DIALOG = 4`: Modal dialog
- `TOOLBAR = 5`: Toolbar window
- `MENU = 6`: Menu window
- `UTILITY = 7`: Utility window
- `SPLASH = 8`: Splash screen

**Example:**
```python
from open_alo_core import WindowType

windows = wm.list_windows()
normal_windows = [w for w in windows if w.window_type == WindowType.NORMAL]
```

---

### FrameType

**Full path**: `open_alo_core.window_manager.FrameType`

Window frame type enumeration.

**Values:**
- `NORMAL = 0`: Normal window with decorations
- `FRAMELESS = 1`: Frameless window (no decorations)

**Example:**
```python
from open_alo_core import FrameType

windows = wm.list_windows()
framed = [w for w in windows if w.frame_type == FrameType.NORMAL]
```

---

## Exceptions

All exceptions inherit from `CoreError` for easy catching.

### CoreError

**Full path**: `open_alo_core.exceptions.CoreError`

Base exception for all core errors.

**Example:**
```python
from open_alo_core import CoreError

try:
    # ... automation code ...
    pass
except CoreError as e:
    print(f"Core error: {e}")
```

### PermissionDenied

**Full path**: `open_alo_core.exceptions.PermissionDenied`

User denied portal permission or insufficient privileges.

**Raised by:**
- `WaylandInput.initialize()`
- `WaylandCapture.capture_screen()`

**Example:**
```python
from open_alo_core import PermissionDenied

try:
    ctrl.initialize(persist_mode=2)
except PermissionDenied:
    print("User denied permission")
```

### CaptureError

**Full path**: `open_alo_core.exceptions.CaptureError`

Screen capture failed.

**Raised by:**
- `WaylandCapture.capture_screen()`

**Example:**
```python
from open_alo_core import CaptureError

try:
    result = capture.capture_screen()
except CaptureError as e:
    print(f"Capture failed: {e}")
```

### InputError

**Full path**: `open_alo_core.exceptions.InputError`

Input injection failed.

**Raised by:**
- `WaylandInput.click()`
- `WaylandInput.move_mouse()`
- `WaylandInput.type_text()`
- `WaylandInput.press_key()`
- `WaylandInput.key_combo()`

**Example:**
```python
from open_alo_core import InputError

try:
    ctrl.click(Point(500, 500))
except InputError as e:
    print(f"Click failed: {e}")
```

### SessionError

**Full path**: `open_alo_core.exceptions.SessionError`

Portal session creation/management failed.

**Raised by:**
- `WaylandInput.initialize()`

**Example:**
```python
from open_alo_core import SessionError

try:
    ctrl.initialize(persist_mode=2)
except SessionError as e:
    print(f"Session error: {e}")
```

### BackendNotAvailable

**Full path**: `open_alo_core.exceptions.BackendNotAvailable`

Requested backend not available on this system.

**Example:**
```python
from open_alo_core import BackendNotAvailable

try:
    # ... initialization ...
    pass
except BackendNotAvailable:
    print("Backend not available on this system")
```

---

## Utilities

### detect_session_type()

**Full path**: `open_alo_core.utils.detect_session_type`

Detect if running in Wayland or X11 session.

**Returns:**
- `"wayland"`: Running on Wayland
- `"x11"`: Running on X11
- `"unknown"`: Cannot determine

**Example:**
```python
from open_alo_core import detect_session_type

session = detect_session_type()
if session == "wayland":
    print("Using Wayland backend")
elif session == "x11":
    print("Using X11 backend")
else:
    print("Unknown session type")
```

---

### is_wayland()

**Full path**: `open_alo_core.utils.is_wayland`

Check if running on Wayland.

**Returns:**
- `bool`: True if WAYLAND_DISPLAY environment variable is set

**Example:**
```python
from open_alo_core import is_wayland

if is_wayland():
    ctrl = WaylandInput()
else:
    raise RuntimeError("Wayland required")
```

---

### is_portal_available()

**Full path**: `open_alo_core.utils.is_portal_available`

Check if XDG Desktop Portal is available.

**Returns:**
- `bool`: True if portal service is running

**Example:**
```python
from open_alo_core import is_portal_available

if not is_portal_available():
    print("Warning: Portal not available")
    print("Cannot initialize input/capture")
```

---

### is_pipewire_available()

**Full path**: `open_alo_core.utils.is_pipewire_available`

Check if PipeWire is available for screen capture.

**Returns:**
- `bool`: True if PipeWire is running

**Example:**
```python
from open_alo_core import is_pipewire_available

if is_pipewire_available():
    print("PipeWire available for capture")
else:
    print("Warning: PipeWire not available")
```

---

### normalize_key()

**Full path**: `open_alo_core.types.normalize_key`

Normalize key name to standard form.

Converts common key aliases to GTK/GDK standard names.

**Parameters:**
- `key` (str): Key name to normalize

**Returns:**
- `str`: Normalized key name

**Example:**
```python
from open_alo_core import normalize_key

# Aliases normalized
normalize_key("enter")    # → "Return"
normalize_key("ctrl")     # → "Control"
normalize_key("esc")      # → "Escape"
normalize_key("win")      # → "Super"

# Already normalized
normalize_key("Return")   # → "Return"
```

---

## Constants

### Mouse Buttons

**Module**: `open_alo_core.types`

```python
BUTTON_LEFT = 1      # Left mouse button
BUTTON_MIDDLE = 2    # Middle mouse button
BUTTON_RIGHT = 3     # Right mouse button
```

**Example:**
```python
from open_alo_core import BUTTON_LEFT, BUTTON_MIDDLE, BUTTON_RIGHT

ctrl.click(Point(500, 500), button=BUTTON_LEFT)    # Left click
ctrl.click(Point(500, 500), button=BUTTON_MIDDLE)  # Middle click
ctrl.click(Point(500, 500), button=BUTTON_RIGHT)   # Right click
```

---

## Complete API Index

### Classes
- `UnifiedRemoteDesktop` ⭐ **RECOMMENDED** - Single permission for input + capture
- `WaylandInput` (Legacy) - Mouse and keyboard control
- `WaylandCapture` (Legacy) - Screen capture
- `WindowManager` - Window management
- `Point` - 2D coordinates
- `Size` - Dimensions
- `Rect` - Rectangle with position and size
- `WindowInfo` - Window information
- `WindowType` - Window type enumeration
- `FrameType` - Frame type enumeration
- `CaptureResult` - Capture result container

### Exceptions
- `CoreError` - Base exception
- `PermissionDenied` - Permission denied
- `CaptureError` - Capture failed
- `InputError` - Input failed
- `SessionError` - Session failed
- `BackendNotAvailable` - Backend unavailable

### Functions
- `detect_session_type()` - Detect Wayland/X11
- `is_wayland()` - Check if Wayland
- `is_portal_available()` - Check portal availability
- `is_pipewire_available()` - Check PipeWire availability
- `normalize_key()` - Normalize key name
- `list_windows()` - List windows (convenience)
- `find_window()` - Find window (convenience)
- `activate_window()` - Activate window (convenience)
- `get_focused_window()` - Get focused window (convenience)

### Constants
- `BUTTON_LEFT` - Left mouse button (1)
- `BUTTON_MIDDLE` - Middle mouse button (2)
- `BUTTON_RIGHT` - Right mouse button (3)

### UnifiedRemoteDesktop Methods (Recommended) ⭐
- `initialize(persist_mode, enable_capture)` → bool - Initialize with one dialog
- `capture_screenshot()` → bytes - Take PNG screenshot
- `get_frame()` → bytes - Get real-time frame
- `get_screen_size()` → (int, int) - Get resolution
- `click(point, button)` - Click at coordinates
- `move_mouse(point)` - Move cursor
- `type_text(text, interval)` - Type text
- `press_key(key)` - Press single key
- `key_combo(keys)` - Press key combination
- `close()` - Release resources

### WaylandInput Methods (Legacy)
- `initialize(persist_mode)` - Initialize session
- `click(point, button)` - Click at coordinates
- `move_mouse(point)` - Move cursor
- `type_text(text, interval)` - Type text
- `press_key(key)` - Press single key
- `key_combo(keys)` - Press key combination
- `close()` - Release resources

### WaylandCapture Methods (Legacy)
- `capture_screen()` - Capture screen
- `close()` - Release resources

### WindowManager Methods

**Listing & Search:**
- `list_windows(current_workspace_only)` - List windows
- `find_window(query, match_title)` - Find window
- `find_all_windows(query, match_title)` - Find all matching
- `get_focused_window()` - Get focused window
- `get_details(window_id)` - Get detailed info
- `get_title(window_id)` - Get window title

**State Management:**
- `activate(window_id)` - Activate window
- `maximize(window_id)` - Maximize
- `unmaximize(window_id)` - Unmaximize
- `minimize(window_id)` - Minimize
- `unminimize(window_id)` - Unminimize
- `close(window_id)` - Close window

**Positioning:**
- `move(window_id, x, y)` - Move window
- `resize(window_id, width, height)` - Resize window
- `move_resize(window_id, x, y, width, height)` - Move and resize
- `get_frame_rect(window_id)` - Get frame rectangle
- `get_frame_bounds(window_id)` - Get frame bounds

**Workspace:**
- `move_to_workspace(window_id, workspace_num)` - Move to workspace

---

## Advanced Usage Examples

### Complete Workflow

```python
from open_alo_core import (
    WaylandInput, WaylandCapture, WindowManager,
    Point, activate_window
)

# 1. Activate target application
activate_window("Text Editor")

# 2. Control input
with WaylandInput() as ctrl:
    ctrl.initialize(persist_mode=2)

    # Click and type
    ctrl.click(Point(500, 500))
    ctrl.type_text("Hello World!")

    # Save with Ctrl+S
    ctrl.key_combo(["Control", "s"])

# 3. Capture screen
with WaylandCapture() as capture:
    result = capture.capture_screen()
    Path("/tmp/screenshot.png").write_bytes(result.data)

print("Workflow complete!")
```

### Window Tiling

```python
from open_alo_core import WindowManager

wm = WindowManager()

# Get windows
editor = wm.find_window("Text Editor")
browser = wm.find_window("Brave")

if editor and browser:
    # Tile left half (1920x1080 screen)
    wm.move_resize(editor.id, 0, 0, 960, 1080)

    # Tile right half
    wm.move_resize(browser.id, 960, 0, 960, 1080)
```

### Automated Testing

```python
from open_alo_core import WaylandInput, WaylandCapture, Point
import time

with WaylandInput() as ctrl:
    ctrl.initialize(persist_mode=2)

    # Test workflow
    steps = [
        (Point(100, 100), "Click button"),
        (Point(200, 200), "Fill form"),
    ]

    for point, description in steps:
        print(f"Step: {description}")
        ctrl.click(point)
        time.sleep(1)

        # Capture result
        with WaylandCapture() as cap:
            result = cap.capture_screen()
            Path(f"/tmp/{description}.png").write_bytes(result.data)
```

---

## Version History

### 0.1.0 (Current)
- Initial release
- Wayland MVP
- Input control via RemoteDesktop Portal
- Screen capture via ScreenCast Portal
- Window management via GNOME Shell D-Bus
- Persistent permission tokens
- Type-safe API with NamedTuples and dataclasses

---

## License

MIT License - See LICENSE file for details

---

## Contributing

Contributions welcome! Please ensure:
- Type hints for all public APIs
- Docstrings with examples
- Error handling with appropriate exceptions
- Tests for new functionality

---

## Support

- **Issues**: GitHub Issues
- **Documentation**: This file
- **Examples**: `examples/` directory
