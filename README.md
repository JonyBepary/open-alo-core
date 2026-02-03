# Open ALO — Desktop Automation for Linux

**Modern Linux desktop automation SDK with Wayland support**

> *"ALO" means "light" in Bengali — This project is dedicated to my maternal grandmother, whom we lovingly called Alo.*

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/open-alo-core)](https://pypi.org/project/open-alo-core/)
[![Platform](https://img.shields.io/badge/platform-Linux-green.svg)](https://www.linux.org/)
[![Wayland](https://img.shields.io/badge/Wayland-Native-brightgreen.svg)](https://wayland.freedesktop.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)

## ⚠️ Prerequisites

- **Operating System:** Linux with Wayland compositor (GNOME, KDE Plasma, Sway)
- **Display Server:** Wayland (X11 is not supported)
- **Python:** 3.10 or higher
- **Desktop Environment:** GNOME Shell recommended (KDE support experimental)

**This library does not work on X11. Wayland is required.**

---

## Features

- **Single Permission Architecture** — One approval for both input and screen capture
- **Real-time Screen Streaming** — Live video frames via PipeWire
- **Input Control** — Mouse movement, clicks, keyboard input, shortcuts
- **Window Management** — Query, focus, and control application windows
- **Persistent Sessions** — Optional permission persistence across restarts
- **Wayland Native** — Built on XDG Portals, PipeWire, and GStreamer
- **Type-Safe API** — Complete type hints for Python 3.10+
- **AI Agent Ready** — Designed for autonomous desktop automation

---

## Quick Start

### Installation

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-pipewire \
    xdg-desktop-portal \
    xdg-desktop-portal-gnome

# Install from PyPI
pip install open-alo-core
# https://pypi.org/project/open-alo-core/
```

**For Window Management (GNOME only):**
1. Install [Window Calls extension](https://extensions.gnome.org/extension/4724/window-calls/) from browser
2. Enable it: `gnome-extensions enable window-calls@domandoman.github.com`

### Basic Usage

```python
from open_alo_core import UnifiedRemoteDesktop, WindowManager, Point

# ONE permission dialog for everything
with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)

    # Screen capture
    screenshot = remote.capture_screenshot()  # PNG bytes
    frame = remote.get_frame()                # Real-time stream
    width, height = remote.get_screen_size()

    # Input control
    remote.click(Point(500, 500))
    remote.type_text("Hello World!\n")
    remote.key_combo(["ctrl", "c"])

# Window management (requires Window Calls extension on GNOME)
wm = WindowManager()
editor = wm.find_window("TextEditor")
wm.activate(editor.id)
```

---

## Examples

```bash
# Minimal example - Quick start
/usr/bin/python3 examples/unified_minimal.py

# Comprehensive demo - Full AI agent workflow
/usr/bin/python3 examples/unified_ai_agent_demo.py

# Window management - Control windows
/usr/bin/python3 examples/window_management_demo.py
```

See [examples/README.md](examples/README.md) for details.

---

## Documentation

- **[API Reference](API_REFERENCE.md)** — Complete API documentation
- **[Quick Reference](docs/UNIFIED_QUICK_REFERENCE.md)** — Common patterns and usage examples
- **[Migration Guide](docs/MIGRATION_TO_UNIFIED.md)** — Upgrading from the legacy two-permission API
- **[Window Management API](docs/WINDOW_MANAGEMENT_API.md)** — GNOME window control reference

---

## Architecture

```
open_alo_core/
├── wayland/
│   ├── unified.py        # UnifiedRemoteDesktop (recommended)
│   ├── input.py          # WaylandInput (legacy)
│   └── capture.py        # WaylandCapture (legacy)
├── window_manager.py     # WindowManager
├── types.py              # Point, Size, Rect, WindowInfo
└── exceptions.py         # Exception hierarchy
```

**UnifiedRemoteDesktop** uses:
- XDG RemoteDesktop Portal (inherits ScreenCast)
- PipeWire for screen streaming
- GStreamer for frame capture
- Single D-Bus session = One permission dialog

---

## AI Agent Example

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

## Why UnifiedRemoteDesktop?

### Legacy Two-Permission Approach
```python
# Required two separate permission dialogs
with WaylandInput() as input:
    input.initialize()  # Permission dialog 1
    with WaylandCapture() as capture:
        capture.initialize()  # Permission dialog 2
        # Both instances required
```

### Unified Single-Permission Approach
```python
# Single permission dialog
with UnifiedRemoteDesktop() as remote:
    remote.initialize(enable_capture=True)  # One permission
    # All functionality available
```

**Advantages:**
- Reduced user friction (matches RustDesk, TeamViewer UX)
- Simplified API surface (single class)
- Industry-standard remote desktop pattern
- Optimized for automated workflows

## Package Structure

### `open_alo_core/` — Core SDK (v0.1.0)
**Primary API for all new projects**

- `UnifiedRemoteDesktop` - Single permission for input + capture
- `WindowManager` - Comprehensive window control
- `WaylandInput`, `WaylandCapture` - Legacy two-permission API
- Full type hints, documentation, examples

### `examples/` - Working Examples
- `unified_minimal.py` - Quick start (20 lines)
- `unified_ai_agent_demo.py` - Full AI agent workflow
- `unified_debug.py` - Troubleshooting version
- `window_management_demo.py` - Window control

### `docs/` - Documentation
- API Reference - Complete API documentation
- Quick Reference - Common patterns
- Migration Guide - Upgrade instructions
- Implementation Details - Technical deep dive

### `archive/` - Legacy Code
- `open_alo/` - Old implementation (v0.3.0)
- Legacy examples using two-permission approach
- Historical documentation

See [archive/README.md](archive/README.md) for migration details.

---

## System Requirements

- **OS**: Linux with Wayland compositor (GNOME, KDE, Sway)
- **Python**: 3.10+
- **Display Server**: Wayland (not X11)
- **Dependencies**:
  - PyGObject (python3-gi)
  - GStreamer 1.0
  - PipeWire
  - XDG Desktop Portal

**Window Management Requirements:**
- GNOME Shell with [Window Calls extension](https://extensions.gnome.org/extension/4724/window-calls/)
- Install extension: Visit link above or use GNOME Extensions app
- Enable extension: `gnome-extensions enable window-calls@domandoman.github.com`

**Tested Environment:**
- Ubuntu 25.10 (Questing)
- Wayland + GNOME Shell / Unity
- Window Calls extension v13+

For architecture and implementation details, see:
- [Architecture Documentation](architecture/UNIFIED_REMOTEDESKTOP_APPROACH.md)
- [Implementation Summary](architecture/UNIFIED_REMOTEDESKTOP_SUMMARY.md)

---

## Contributing

Contributions welcome! This project will be open-sourced soon.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **RustDesk** - Inspiration for single-permission approach
- **XDG Portals** - Secure desktop integration
- **PipeWire** - Modern screen capture
- **GNOME Project** - Window management APIs

---

## In Loving Memory

*This project is dedicated to my maternal grandmother, **Alo** — whose name means "light" in Bengali.*

She did so much for me throughout my life, but in her final years, I couldn't do as much for her as I wished. After I lost her, I truly realized what I had lost.

The only thing I'm good at is coding. On the morning after her burial, in a moment of grief where the mind tries to distract itself from reality, I vaguely outlined this project. I decided then that it would be dedicated to her.

It's been almost half a year now, and I've finally managed to push a very basic MVP. It may end up buried among my other unfinished projects. It will probably only support GNOME Wayland. But with my current capabilities, perhaps this is all I can dedicate to her memory.

*Rest in peace, Nani.*
