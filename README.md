<div align="center">

# <img src="assets/logo_icon.svg" width="36" height="36" alt=""> open-alo-core

**High-Performance Wayland Desktop Automation SDK for Linux & Autonomous AI Agents**  
*Single Permission • Real-Time PipeWire Streaming • Deterministic Input Injection • Zero AI/ML Dependencies*

</div>

<p align="center">
  <a href="https://pypi.org/project/open-alo-core/"><img src="https://img.shields.io/pypi/v/open-alo-core?color=blue&label=PyPI" alt="PyPI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://wayland.freedesktop.org/"><img src="https://img.shields.io/badge/Wayland-Native-ffbc00?logo=wayland&logoColor=black" alt="Wayland"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/Tests-328%20Passed-success" alt="Tests">
</p>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#architectural-highlights">Architecture</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#api-reference">API Surface</a> •
  <a href="#examples">Examples</a> •
  <a href="#contributing">Contributing</a>
</p>

---

> *"ALO" translates to "light" in Bengali — dedicated to the memory of my grandmother, whom we affectionately called Alo.*

---

## Overview

**`open-alo-core`** is a standalone, lightweight, and hardware-near desktop automation substrate engineered specifically for modern Linux Wayland environments. Built on top of the **XDG Desktop Portal (`org.freedesktop.portal.RemoteDesktop`)** and **PipeWire / GStreamer**, it unifies screen capture and pointer/keyboard control under a **single user permission dialog**.

Designed with zero AI/ML dependencies, `open-alo-core` serves as the rock-solid foundation for desktop robotics, GUI automation frameworks, remote control servers, and visual RL/LLM agents.

---

## Architectural Highlights

<table>
<tr>
<td width="50%" valign="top">

### 🔐 Unified Single-Permission Model
Traditional Wayland automation tools require separate permissions for ScreenCast and Input injection, disrupting automated workflows. `open-alo-core` acquires a single joint session handle with persistent restore tokens:
```python
from open_alo_core import UnifiedRemoteDesktop, Point

with UnifiedRemoteDesktop() as desktop:
    desktop.initialize(persist_mode=2, enable_capture=True)
    obs = desktop.capture_observation()
    desktop.click(Point(500, 300))
    desktop.type_text("Hello from Wayland!")
```

</td>
<td width="50%" valign="top">

### 🪟 GNOME Shell Window Management
Direct D-Bus integration with GNOME Shell provides deterministic window lifecycle control without legacy X11 hacks:
- Window discovery by PID, `wm_class`, or title.
- Real-time z-order stacking inspection.
- Window activation, focus raising, and geometry manipulation (`move_resize`, `maximize`, `minimize`).
- Standalone noise/utility window filtering (`is_utility_window`).

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📐 Typed Stream Geometry
The `StreamGeometry` dataclass encapsulates capture stream properties, multi-monitor origins, scaling factors, and boundary transformations:
- `rect`: Global stream bounding box.
- `is_in_stream(rect)`: Strict viewport intersection check.
- `clamp_to_stream(rect)`: Multi-monitor bounding box containment.
- `stream_to_global_point(pt)` / `global_to_stream_point(pt)`: Seamless coordinate space translation.

</td>
<td width="50%" valign="top">

### 🛡️ Pure Geometric Preflight
The `GeometricPreflight` validator enforces coordinate integrity and spatial occlusion safety before any hardware input injection:
- Fail-closed out-of-bounds rejection.
- Sentinel value protection (e.g., `-2147483648`).
- Real-time z-order occlusion analysis against overlapping foreground windows.

</td>
</tr>
</table>

---

## Installation

### 1. System Dependencies (Ubuntu / Debian)

```bash
sudo apt update
sudo apt install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-pipewire \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    xdg-desktop-portal \
    xdg-desktop-portal-gnome
```

### 2. Python Package Installation

```bash
pip install open-alo-core
```

*Or install from source in editable mode:*
```bash
git clone https://github.com/JonyBepary/VisualAgent.git
cd VisualAgent/OPEN_ALO
pip install -e .
```

### 3. Window Management Extension (Optional, GNOME Shell)

For advanced window placement and z-order inspection, install and enable the [Window Calls](https://extensions.gnome.org/extension/4724/window-calls/) extension:
```bash
gnome-extensions enable window-calls@domandoman.github.com
```

---

## Quick Start

### Basic Desktop Interaction

```python
from open_alo_core import UnifiedRemoteDesktop, Point, normalize_key

with UnifiedRemoteDesktop() as desktop:
    # Initialize joint input + capture session
    desktop.initialize(persist_mode=2, enable_capture=True)

    # 1. Capture observation with lockstep timestamp
    obs = desktop.capture_observation()
    png_bytes = obs["png"]
    timestamp_ns = obs["timestamp_ns"]
    stream_geom = obs["stream_info"]  # StreamGeometry instance

    # 2. Pointer operations
    desktop.click(Point(640, 480))
    desktop.double_click(Point(640, 480))

    # 3. Keyboard input
    desktop.type_text("Autonomous Linux Automation")
    desktop.key_combo(["Control", "s"])
```

### Window Management & Occlusion Preflight

```python
from open_alo_core import WindowManager, GeometricPreflight, Point

wm = WindowManager()
preflight = GeometricPreflight()

# Locate application window
editor = wm.find_window("Text Editor")
if editor:
    # Raise and focus target window
    wm.activate(editor.id)
    wm.move_resize(editor.id, x=100, y=100, width=1280, height=800)

    # Query desktop z-order and window rects
    z_order = wm.get_window_z_order()
    window_rects = {w.id: wm.get_frame_rect(w.id) for w in wm.list_windows()}

    # Verify target point is not occluded by a foreground window
    target_pt = Point(250, 250)
    verdict = preflight.verify_point_occlusion(target_pt, editor.id, window_rects, z_order)
    if verdict.is_safe:
        print("Target point is clear for interaction.")
```

---

## API Reference

### Core Modules & Exports

| Class / Function | Module | Description |
|---|---|---|
| **`UnifiedRemoteDesktop`** | `open_alo_core.wayland.unified` | Primary unified interface for PipeWire video streaming, screenshot acquisition, and Wayland input injection. |
| **`StreamGeometry`** | `open_alo_core.types` | Immutable dataclass defining stream dimensions, logical scaling, origin offsets, and coordinate translation. |
| **`GeometricPreflight`** | `open_alo_core.preflight` | Low-level geometric preflight verifier for coordinate boundary checks and z-order window occlusion. |
| **`WindowManager`** | `open_alo_core.window_manager` | GNOME Shell D-Bus interface for window discovery, geometry manipulation, activation, and z-order inspection. |
| **`is_utility_window`** | `open_alo_core.window_manager` | Standalone predicate identifying desktop background actors, XWayland dummies, and noise windows. |
| **`AffineTransform2D`** | `open_alo_core.geometry` | 2D affine mapping matrix for calibrating between AT-SPI accessibility coordinate spaces and OS screen pixels. |
| **`Point`**, **`Rect`**, **`Size`** | `open_alo_core.types` | Zero-overhead immutable geometric primitives with containment and centering helpers. |

---

## Examples & Showcase Suite

The [`examples/`](examples/) directory contains 6 intentional, self-contained showcase modules:

- [`examples/00_environment_doctor/`](examples/00_environment_doctor/): Zero-permission diagnostic probe for Wayland, portals, clocks, and geometry sanitization.
- [`examples/01_unified_session_capture/`](examples/01_unified_session_capture/): Single-permission capture workflow (typed `StreamGeometry`, screenshots, live frames, and raw RGB).
- [`examples/02_input_surface_tour/`](examples/02_input_surface_tour/): Full input injection surface with preflight-gated bounds and occlusion safety.
- [`examples/03_window_orchestra/`](examples/03_window_orchestra/): Complete GNOME window management surface with z-order stacking, workspace migrations, and state restoration.
- [`examples/04_calibration_workbench/`](examples/04_calibration_workbench/): Sub-pixel coordinate calibration, affine solving, and drift demotion policies.
- [`examples/05_legacy_backends_compare/`](examples/05_legacy_backends_compare/): Feature and architecture comparison across Wayland capture and input backends.

---

## Verification & Testing

The `open-alo-core` test suite includes unit tests, integration mocks, and invariant checkers:

```bash
pytest tests/ -v
```

```
============================= 328 passed in 3.88s ==============================
```

---

## Contributing

We welcome contributions, issues, and pull requests. Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and code standards.

---

## License

This project is licensed under the [MIT License](LICENSE).

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
