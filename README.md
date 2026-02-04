<p align="center">
  <img src="assets/logo.png" alt="Open ALO" width="600" style="border-radius: 12px;">
</p>

<h1 align="center">Open ALO</h1>

<p align="center">
  <strong>Desktop Automation for Linux</strong><br>
  <em>Single permission • Real-time capture • Full control</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/open-alo-core/"><img src="https://img.shields.io/pypi/v/open-alo-core?color=blue&label=PyPI" alt="PyPI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://wayland.freedesktop.org/"><img src="https://img.shields.io/badge/Wayland-Native-ffbc00?logo=wayland&logoColor=black" alt="Wayland"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"></a>
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="API_REFERENCE.md">API Reference</a> •
  <a href="#examples">Examples</a>
</p>

---

> *"ALO" means "light" in Bengali — dedicated to my grandmother, whom we lovingly called Alo.*

---

## Why Open ALO?

Most Linux automation tools require **multiple permission dialogs** or don't work on Wayland at all. Open ALO uses the **RemoteDesktop Portal** — the same approach as RustDesk and TeamViewer — to provide:

<table>
<tr>
<td width="50%">

**One Permission Dialog**
```python
with UnifiedRemoteDesktop() as remote:
    remote.initialize()  # ← Single approval

    # Everything available:
    remote.capture_screenshot()
    remote.click(Point(100, 200))
    remote.type_text("Hello!")
```

</td>
<td width="50%">

**Old Approach (Two Dialogs)**
```python
with WaylandInput() as input:
    input.initialize()  # Dialog 1
    with WaylandCapture() as capture:
        capture.initialize()  # Dialog 2
        # Finally can use both...
```

</td>
</tr>
</table>

---

## Features

| Feature                   | Description                                    |
| ------------------------- | ---------------------------------------------- |
| 🖥️ **Screen Capture**      | Real-time streaming via PipeWire + Screenshots |
| 🖱️ **Mouse Control**       | Click, move, scroll at any coordinate          |
| ⌨️ **Keyboard Input**      | Type text, press keys, execute shortcuts       |
| 🪟 **Window Management**   | Find, focus, move windows (GNOME)              |
| 🔐 **Single Permission**   | One dialog for everything                      |
| 💾 **Persistent Sessions** | Approve once, run forever                      |
| 🐍 **Type-Safe**           | Full type hints for modern Python              |

---

## Requirements

<table>
<tr>
<td>

**Platform**
- Linux with Wayland
- GNOME, KDE Plasma, or Sway
- X11 is **not supported**

</td>
<td>

**Python**
- Python 3.10+
- PyGObject
- GStreamer 1.0

</td>
<td>

**Window Management**
- GNOME Shell only
- [Window Calls extension](https://extensions.gnome.org/extension/4724/window-calls/)

</td>
</tr>
</table>

---

## Installation

```bash
# System dependencies (Ubuntu/Debian)
sudo apt install python3-gi python3-gi-cairo \
    gir1.2-gst-plugins-base-1.0 gstreamer1.0-pipewire \
    xdg-desktop-portal xdg-desktop-portal-gnome

# Install from PyPI
pip install open-alo-core
```

<details>
<summary><strong>Window Management Setup (GNOME only)</strong></summary>

1. Install [Window Calls extension](https://extensions.gnome.org/extension/4724/window-calls/)
2. Enable it:
   ```bash
   gnome-extensions enable window-calls@domandoman.github.com
   ```

</details>

---

## Quick Start

```python
from open_alo_core import UnifiedRemoteDesktop, WindowManager, Point

# Initialize with single permission dialog
with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)

    # Capture screen
    screenshot = remote.capture_screenshot()
    width, height = remote.get_screen_size()

    # Control input
    remote.click(Point(500, 300))
    remote.type_text("Automated with Open ALO!")
    remote.key_combo(["ctrl", "s"])

# Window management
wm = WindowManager()
window = wm.find_window("Firefox")
wm.activate(window.id)
```

---

## Examples

| Example                                                           | Description             |
| ----------------------------------------------------------------- | ----------------------- |
| [`unified_minimal.py`](examples/unified_minimal.py)               | Quick start in 20 lines |
| [`unified_ai_agent_demo.py`](examples/unified_ai_agent_demo.py)   | Full AI agent workflow  |
| [`window_management_demo.py`](examples/window_management_demo.py) | Window control patterns |

```bash
python3 examples/unified_ai_agent_demo.py
```

---

## AI Agent Integration

```python
from open_alo_core import UnifiedRemoteDesktop, Point

with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)

    while running:
        frame = remote.get_frame()           # Get screen
        action = ai_model.decide(frame)      # AI decides

        if action.type == "click":
            remote.click(Point(action.x, action.y))
        elif action.type == "type":
            remote.type_text(action.text)
```

---

## Documentation

| Document                                           | Description                   |
| -------------------------------------------------- | ----------------------------- |
| [API Reference](API_REFERENCE.md)                  | Complete method documentation |
| [Quick Reference](docs/UNIFIED_QUICK_REFERENCE.md) | Common patterns               |
| [Migration Guide](docs/MIGRATION_TO_UNIFIED.md)    | Upgrade from legacy API       |
| [Troubleshooting](TROUBLESHOOTING.md)              | Common issues and solutions   |
| [Architecture](architecture/)                      | Implementation details        |

---

## Project Structure

```
open-alo/
├── src/open_alo_core/     # Core SDK
│   ├── wayland/           # Portal implementations
│   │   └── unified.py     # UnifiedRemoteDesktop
│   ├── window_manager.py  # GNOME window control
│   └── types.py           # Point, Size, Rect, WindowInfo
├── examples/              # Working examples
├── docs/                  # User documentation
└── architecture/          # Technical documentation
```

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/JonyBepary/Open-ALO.git
cd Open-ALO
pip install -e .
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **RustDesk** — Inspiration for single-permission architecture
- **XDG Portals** — Secure Wayland integration
- **PipeWire** — Modern Linux multimedia
- **GNOME Project** — Window management APIs

---

<p align="center">
  <em>
    This project is dedicated to my maternal grandmother, <strong>Alo</strong> — whose name means "light" in Bengali.
  </em>
</p>

<p align="center">
  <em>
    She did so much for me throughout my life. After losing her, I realized what I had lost.<br>
    The only thing I'm good at is coding — so this project is my dedication to her memory.
  </em>
</p>

<p align="center">
  <strong>Rest in peace, Nani.</strong>
</p>
