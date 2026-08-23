# Changelog

All notable changes to OPEN_ALO (`open-alo-core`) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-08-23

### Major Release — Substrate Hardening, StreamGeometry, GeometricPreflight, and Advanced Window Operations

This milestone release transforms `open-alo-core` into an industrial-grade Wayland automation substrate and standalone SDK for autonomous visual agents, remote robotics, and system scripting.

### Added

#### 1. Unified Single-Permission Substrate (`UnifiedRemoteDesktop`)
- **Single Permission Dialog**: Merges PipeWire video capture and Wayland input injection under a single authorization prompt via `org.freedesktop.portal.RemoteDesktop`.
- **Persistent Restore Tokens**: Saves session tokens to disk, eliminating permission prompts on subsequent runs.
- **Lockstep Observation Capture**: `capture_observation()` returns raw RGB buffers, PNG frames, monotonic timestamps (`timestamp_ns`), and typed `StreamGeometry`.

#### 2. Typed Stream Geometry (`StreamGeometry`)
- **Multi-Monitor Spatial Mapping**: Encapsulates stream dimensions, monitor origin offsets, and scaling factors.
- **Boundary & Containment Helpers**: `is_in_stream(rect)` and `clamp_to_stream(rect)` for viewport bounds enforcement.
- **Coordinate Space Transformations**: `global_to_stream_point()` and `stream_to_global_point()` for seamless display coordinate conversions.

#### 3. Pure Geometric Preflight (`GeometricPreflight`)
- **Fail-Closed Safety Engine**: Validates coordinates before physical hardware injection.
- **Sentinel Rejection**: Rejects uninitialized sentinels (e.g. `-2147483648`).
- **Z-Order Occlusion Analysis**: Validates that target coordinates are not occluded by foreground windows.

#### 4. Advanced Window Management (`WindowManager` & `window-actions` v1.17)
- **Stacking Z-Order Inspection**: `get_window_z_order()` returns compositor window stacking order (bottom-to-top).
- **Utility Window Filtering**: Standalone `is_utility_window()` and `include_utility=False` filter out XWayland dummy actors and Desktop Icons NG layers.
- **Always-on-Top Control**: `make_above(winid)` and `unmake_above(winid)` methods with convenience wrappers (`make_window_above`, `unmake_window_above`).
- **Full-Screen Operations**: `make_fullscreen(winid)`, `unmake_fullscreen(winid)`, and `toggle_fullscreen(winid)`.
- **Enriched `WindowInfo` Model**: Exposes `fullscreen`, `minimized`, `maximized_horizontally`, `maximized_vertically`, and `above` boolean states.
- **GNOME Shell 50 Support**: Full compatibility with GNOME Shell 45 through 50.

#### 5. Coordinate Calibration Engine (`AffineTransform2D`)
- **Sub-Pixel Mapping**: Computes least-squares affine transformations between AT-SPI accessibility coordinate trees and physical display pixels.
- **Residual Calculation**: `residual()` and `RESIDUAL_LIMIT_PX` for runtime drift detection.

#### 6. Capability Showcase Test & Demonstration Suite
- **`00_environment_doctor`**: Zero-permission system diagnostic probe (22 tests).
- **`01_unified_session_capture`**: Single-permission capture demonstration (4 tests).
- **`02_input_surface_tour`**: Preflight-gated pointer and keyboard injection (5 tests).
- **`03_window_orchestra`**: State-restoring window manipulation orchestra (4 tests).
- **`04_calibration_workbench`**: Affine coordinate mapping workbench (10 tests).
- **`05_legacy_backends_compare`**: Direct performance and architecture comparison (4 tests).

### Changed
- Refactored `WindowManager` D-Bus parsing to handle double-quoted and single-quoted response tuples across all GNOME Shell versions.
- Exported all core primitives (`StreamGeometry`, `GeometricPreflight`, `AffineTransform2D`, `is_utility_window`) in top-level `open_alo_core`.

### Quality & Testing
- **328 Unit Tests (90% Test Coverage)**: Full mock D-Bus and portal infrastructure (`pytest tests/`).
- **49 Showcase Tests**: Headless verification of all showcase modules (`pytest examples/`).
- **100% Benchmark Completion**: Verified on live Wayland desktop across text editors, file managers, and browser tasks.

---

## [0.2.0] - 2026-02-01

### Added
- Initial PipeWire capture module
- Clipboard synchronization module
- Remote desktop server module
- Comprehensive test suite

---

## [0.1.0] - 2026-02-01

### Added
- Initial release of WaylandBackend with persistent permissions
- SmartWaylandBackend with window management
- Input injection via XDG Portal
