# open-alo-core

**High-Performance Wayland Desktop Automation SDK for Linux & Autonomous AI Agents**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Linux-green.svg)](https://www.linux.org/)
[![Wayland](https://img.shields.io/badge/Wayland-Native-brightgreen.svg)](https://wayland.freedesktop.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)
[![PyPI](https://img.shields.io/pypi/v/open-alo-core?color=orange&label=PyPI)](https://pypi.org/project/open-alo-core/)

Desktop automation SDK for Linux Wayland with **one permission dialog** for both real-time PipeWire screen capture and deterministic input control.

## ✨ Core Features

- ✅ **Single Permission Substrate** - Joint authorization for input injection + PipeWire capture via `org.freedesktop.portal.RemoteDesktop`.
- ✅ **Typed Stream Geometry** - `StreamGeometry` with multi-monitor offset handling, bounding box clamping, and coordinate transformations.
- ✅ **Geometric Preflight Safety** - `GeometricPreflight` for out-of-bounds sentinel rejection and z-order window occlusion validation.
- ✅ **GNOME Shell Window Control** - Find, activate, move, resize, stack (z-order), full-screen, and keep-on-top window operations.
- ✅ **Sub-Pixel Coordinate Calibration** - `AffineTransform2D` least-squares affine solver for AT-SPI accessibility coordinate mapping.
- ✅ **Zero AI/ML Dependencies** - Hardware-near Python abstraction.

## 🚀 Quick Start

### Installation

```bash
# System dependencies (Ubuntu/Debian)
sudo apt install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-pipewire \
    xdg-desktop-portal \
    xdg-desktop-portal-gnome

# Install from PyPI
pip install open-alo-core
```

### Basic Usage

```python
from open_alo_core import UnifiedRemoteDesktop, Point

# Single permission dialog initializes both input & screencast
with UnifiedRemoteDesktop() as desktop:
    desktop.initialize(persist_mode=2, enable_capture=True)

    # Observation capture
    obs = desktop.capture_observation()
    png_bytes = obs["png"]
    stream_geom = obs["stream_info"]  # StreamGeometry instance

    # Input injection
    desktop.click(Point(500, 300))
    desktop.type_text("Autonomous Linux Automation")
    desktop.key_combo(["Control", "s"])
```

### Window Management & Occlusion Preflight

```python
from open_alo_core import WindowManager, GeometricPreflight, Point

wm = WindowManager()
preflight = GeometricPreflight()

editor = wm.find_window("Text Editor")
if editor:
    wm.activate(editor.id)
    wm.make_above(editor.id)

    z_order = wm.get_window_z_order()
    window_rects = {w.id: wm.get_frame_rect(w.id) for w in wm.list_windows()}

    verdict = preflight.verify_point_occlusion(Point(200, 200), editor.id, window_rects, z_order)
    if verdict.is_safe:
        print("Target coordinate is clear of occlusion.")
```

## 📋 System Requirements

- **OS**: Linux with Wayland (GNOME, KDE Plasma, Sway)
- **Python**: 3.10+
- **Compositor Support**: XDG Desktop Portals + PipeWire
- **Window Management**: GNOME Shell + [window-actions extension](https://github.com/JonyBepary/window-actions)

## 📄 License

MIT License — see [LICENSE](LICENSE)

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
