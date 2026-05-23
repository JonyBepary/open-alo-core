# Open ALO

**Desktop Automation for Linux**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Linux-green.svg)](https://www.linux.org/)
[![Wayland](https://img.shields.io/badge/Wayland-Native-brightgreen.svg)](https://wayland.freedesktop.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-v0.1.0-orange.svg)](https://pypi.org/project/open-alo-core/)

Desktop automation library for Linux with **one permission dialog** for both screen capture and input control. Perfect for AI agents, RPA, and testing.

## ✨ Features

- ✅ **Single Permission Dialog** - One approval for input + capture (RustDesk-style)
- ✅ **Real-time Screen Streaming** - Live frames via PipeWire
- ✅ **Full Input Control** - Mouse, keyboard, shortcuts
- ✅ **Window Management** - Find, activate, control windows (GNOME)
- ✅ **Persistent Sessions** - Approve once, run forever
- ✅ **Wayland Native** - XDG Portals, PipeWire, GStreamer
- ✅ **Type-Safe** - Full type hints
- ✅ **Zero ML Dependencies** - Pure hardware abstraction

## 🚀 Quick Start

### Installation

```bash
# System dependencies (Ubuntu/Debian)
sudo apt install \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-pipewire \
    xdg-desktop-portal \
    xdg-desktop-portal-gnome

# Install from PyPI
pip install open-alo-core
```

**For Window Management (GNOME only):**
1. Install [Window Calls extension](https://extensions.gnome.org/extension/4724/window-calls/) from browser
2. Enable it: `gnome-extensions enable window-calls@domandoman.github.com`

### Basic Usage

```python
from open_alo_core import UnifiedRemoteDesktop, Point

# ONE permission dialog for everything!
with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)

    # Screen capture
    screenshot = remote.capture_screenshot()  # PNG bytes
    frame = remote.get_frame()                # Live frame
    width, height = remote.get_screen_size()

    # Input control
    remote.click(Point(500, 500))
    remote.type_text("Hello World!\n")
    remote.key_combo(["ctrl", "c"])
```

### Window Management (GNOME)

```python
from open_alo_core import WindowManager

wm = WindowManager()
editor = wm.find_window("Text Editor")
wm.activate(editor.id)
wm.maximize(editor.id)
```

## 📋 System Requirements

- **OS**: Linux with Wayland (GNOME, KDE, Sway)
- **Python**: 3.10+
- **Dependencies**: PyGObject, GStreamer 1.0, PipeWire
- **Window Management**: GNOME Shell + [Window Calls extension](https://extensions.gnome.org/extension/4724/window-calls/)

**Tested on:**
- Ubuntu 25.10 (Questing), Wayland + GNOME/Unity
- Window Calls extension v13+

## 📚 Documentation

- [**API Reference**](https://github.com/JonyBepary/Open-ALO/blob/main/API_REFERENCE.md) - Complete API documentation
- [**Quick Reference**](https://github.com/JonyBepary/Open-ALO/blob/main/docs/UNIFIED_QUICK_REFERENCE.md) - Common patterns
- [**Examples**](https://github.com/JonyBepary/Open-ALO/tree/main/examples/) - Working code examples
- [**Migration Guide**](https://github.com/JonyBepary/Open-ALO/blob/main/docs/MIGRATION_TO_UNIFIED.md) - Upgrade from legacy

## 🎯 Use Cases

- **AI Agents** - Screen understanding + autonomous control
- **RPA** - Robotic process automation
- **Testing** - UI testing and automation
- **Monitoring** - Screenshot capture and analysis
- **Remote Control** - Desktop automation over network

## 🏗️ Architecture

```
UnifiedRemoteDesktop
├── RemoteDesktop Portal (org.freedesktop.portal.RemoteDesktop)
│   ├── Input Control (keyboard, mouse)
│   └── Inherits ScreenCast (screen capture)
├── PipeWire (real-time streaming)
└── GStreamer (frame processing)

WindowManager
└── Window Calls Extension (GNOME D-Bus)
```

## 🔒 Security

- Uses XDG Desktop Portals (sandboxed)
- Permission dialogs via system compositor
- Persistent tokens stored in `~/.config/open_alo_core/`
- No root required

## 📄 License

MIT License - See [LICENSE](LICENSE) file

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](https://github.com/JonyBepary/Open-ALO/blob/main/CONTRIBUTING.md) for guidelines.

## 🐛 Issues

Report bugs at: https://github.com/JonyBepary/Open-ALO/issues

## 🌟 Credits

Developed by OPEN_ALO Contributors

---

**Repository**: https://github.com/JonyBepary/Open-ALO
