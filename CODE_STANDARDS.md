# Code Standards for open-alo-core

## Naming Conventions (PEP 8 Compliant ✅)

Our codebase follows [PEP 8](https://peps.python.org/pep-0008/) naming conventions:

### Classes
- **PascalCase** (CapWords)
- Examples: `UnifiedRemoteDesktop`, `WindowManager`, `Point`, `CoreError`

```python
class UnifiedRemoteDesktop:
    pass

class WindowInfo:
    pass
```

### Functions and Methods
- **snake_case** (lowercase with underscores)
- Examples: `capture_screenshot()`, `get_frame()`, `find_window()`

```python
def capture_screenshot() -> bytes:
    pass

def find_window(query: str) -> Optional[WindowInfo]:
    pass
```

### Variables and Parameters
- **snake_case**
- Examples: `session_handle`, `pipewire_node`, `current_workspace_only`

```python
session_handle = None
pipewire_node = 12345
current_workspace_only = False
```

### Constants
- **UPPER_CASE** with underscores
- Examples: `BUTTON_LEFT`, `DEVICE_KEYBOARD`, `SOURCE_MONITOR`

```python
BUTTON_LEFT = 1
BUTTON_MIDDLE = 2
BUTTON_RIGHT = 3
```

### Private/Protected Members
- **Leading underscore** for internal use
- Examples: `_bus`, `_portal`, `_ensure_dbus()`

```python
class UnifiedRemoteDesktop:
    def __init__(self):
        self._bus = None  # Private attribute
        self._portal = None

    def _ensure_dbus(self):  # Private method
        pass
```

### Module Names
- **snake_case** (lowercase with underscores)
- Examples: `unified.py`, `window_manager.py`, `exceptions.py`

```
src/open_alo_core/
├── __init__.py
├── types.py
├── exceptions.py
├── window_manager.py
└── wayland/
    ├── unified.py
    ├── capture.py
    └── input.py
```

## Type Hints

All public APIs have complete type hints:

```python
def click(self, point: Point, button: int = 1) -> None:
    """Click at screen coordinates"""
    pass

def get_frame(self) -> bytes:
    """Get current frame from stream"""
    pass

def list_windows(self, current_workspace_only: bool = False) -> List[WindowInfo]:
    """List all open windows"""
    pass
```

## Docstrings

All public classes and methods have docstrings:

```python
class UnifiedRemoteDesktop:
    """
    Unified remote desktop session using RemoteDesktop portal.

    Provides both input control AND screen capture in a single permission.
    Perfect for AI agents that need to see and control the desktop.
    """

    def initialize(self, persist_mode: int = 2, enable_capture: bool = True) -> bool:
        """
        Initialize unified remote desktop session

        Args:
            persist_mode: Permission persistence (0=transient, 1=app, 2=explicit)
            enable_capture: Enable screen capture (PipeWire)

        Returns:
            True if successful, False otherwise

        Example:
            >>> remote = UnifiedRemoteDesktop()
            >>> remote.initialize(persist_mode=2)
            True
        """
        pass
```

## Import Organization

Imports are organized in standard order:

```python
# Standard library
import json
import time
from pathlib import Path
from typing import Optional, List, Tuple

# Third-party
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Local
from ..types import Point
from ..exceptions import PermissionDenied
```

## File Structure

```
open_alo_core/
├── pyproject.toml          # Package metadata
├── README.md               # PyPI description
├── LICENSE                 # MIT license
├── MANIFEST.in             # Package data
├── PUBLISHING.md           # This file
└── src/
    └── open_alo_core/
        ├── __init__.py     # Public API exports
        ├── types.py        # Data types (Point, Size, Rect)
        ├── exceptions.py   # Exception hierarchy
        ├── window.py       # Legacy window functions
        ├── window_manager.py  # WindowManager class
        ├── utils/
        │   └── __init__.py # Utility functions
        └── wayland/
            ├── __init__.py
            ├── unified.py  # UnifiedRemoteDesktop
            ├── capture.py  # WaylandCapture (legacy)
            └── input.py    # WaylandInput (legacy)
```

## Code Quality Checklist

- [x] PEP 8 naming conventions
- [x] Type hints on all public APIs
- [x] Docstrings on all public classes/functions
- [x] Organized imports (stdlib → third-party → local)
- [x] No unused imports
- [x] No `import *`
- [x] Context managers for resource cleanup
- [x] Error handling with custom exceptions
- [x] Consistent code style

## Testing Standards

```python
# Test file naming: test_*.py
# Test class naming: Test<Feature>
# Test method naming: test_<feature>_<scenario>

class TestUnifiedRemoteDesktop:
    def test_initialization_success(self):
        pass

    def test_capture_screenshot_png(self):
        pass

    def test_click_valid_coordinates(self):
        pass
```

## Version Consistency

Keep version numbers synchronized:

1. `pyproject.toml` → `version = "0.1.0"`
2. `src/open_alo_core/__init__.py` → `__version__ = "0.1.0"`
3. `API_REFERENCE.md` → `**Version:** 0.1.0`
4. Git tag → `v0.1.0`

## API Stability

- **Stable**: `UnifiedRemoteDesktop`, `WindowManager`, `Point`, `Size`, `Rect`
- **Legacy**: `WaylandInput`, `WaylandCapture` (still supported)
- **Internal**: Any `_prefixed` names (may change)

## Documentation Standards

1. Every public class/function has a docstring
2. All parameters documented in docstring
3. Return types documented
4. Examples included for complex APIs
5. Type hints match docstring descriptions

---

**Summary**: The codebase already follows PEP 8 and Python best practices. All naming is consistent and professional. Ready for PyPI publication! 🚀
