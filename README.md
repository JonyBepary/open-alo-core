# OPEN_ALO - Linux Desktop Automation for AI Agents

**Modern desktop automation SDK for Linux with single-permission UX**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Linux-green.svg)](https://www.linux.org/)
[![Wayland](https://img.shields.io/badge/Wayland-Native-brightgreen.svg)](https://wayland.freedesktop.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)

---

## 🌟 Features

- **✅ Single Permission Dialog** - One approval for both input and screen capture (like RustDesk)
- **✅ Real-time Screen Streaming** - Live frames for AI agents
- **✅ Input Control** - Mouse, keyboard, shortcuts
- **✅ Window Management** - Find, activate, control windows
- **✅ Persistent Sessions** - Approve once, run forever
- **✅ Wayland Native** - Uses XDG Portals, PipeWire, GStreamer
- **✅ Type-Safe** - Full type hints and modern Python
- **✅ AI-Ready** - Perfect for screen-reading agents

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd OPEN_ALO

# Install system dependencies (Ubuntu/Debian)
sudo apt install \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-pipewire \
    xdg-desktop-portal \
    xdg-desktop-portal-gnome

# Install package
cd open_alo_core
pip install -e .
```

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

# Window management (independent)
wm = WindowManager()
editor = wm.find_window("TextEditor")
wm.activate(editor.id)
```

---

## 🎯 Examples

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

## 📖 Documentation

- **[API Reference](open_alo_core/API_REFERENCE.md)** - Complete API documentation
- **[Quick Reference](docs/UNIFIED_QUICK_REFERENCE.md)** - Common patterns and examples
- **[Migration Guide](docs/MIGRATION_TO_UNIFIED.md)** - Upgrade from legacy API
- **[Implementation Details](docs/UNIFIED_REMOTEDESKTOP_SUMMARY.md)** - Technical deep dive

---

## 🏗️ Architecture

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

## 🤖 AI Agent Example

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

## 🆚 Why UnifiedRemoteDesktop?

### Old Approach (Legacy)
```python
# TWO permission dialogs ❌
with WaylandInput() as input:
    input.initialize()  # Dialog 1
    with WaylandCapture() as capture:
        capture.initialize()  # Dialog 2
        # Use both...
```

### New Approach (Unified)
```python
# ONE permission dialog ✅
with UnifiedRemoteDesktop() as remote:
    remote.initialize(enable_capture=True)  # Dialog 1 only!
    # Everything available
```

**Benefits:**
- ✅ Better UX (one dialog like RustDesk)
- ✅ Simpler code (single class)
- ✅ Industry standard approach
- ✅ Perfect for AI agents

## 📦 What's Inside

### `open_alo_core/` - Modern SDK (v0.1.0) ⭐
**Recommended for all new development**

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

## 🛠️ System Requirements

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

---

## 📚 Documentation

- **[API Reference](API_REFERENCE.md)** - Complete API docs
- **[Quick Reference](docs/UNIFIED_QUICK_REFERENCE.md)** - Common patterns
- **[Examples Guide](examples/README.md)** - All examples
- **[Migration Guide](docs/MIGRATION_TO_UNIFIED.md)** - Upgrade from legacy

Technical deep dives:
- [UnifiedRemoteDesktop Approach](docs/UNIFIED_REMOTEDESKTOP_APPROACH.md)
- [Implementation Summary](docs/UNIFIED_REMOTEDESKTOP_SUMMARY.md)

---

## 🤝 Contributing

Contributions welcome! This project will be open-sourced soon.

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **RustDesk** - Inspiration for single-permission approach
- **XDG Portals** - Secure desktop integration
- **PipeWire** - Modern screen capture
- **GNOME Project** - Window management APIs
