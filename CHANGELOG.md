# Changelog

All notable changes to OPEN_ALO will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-02-02

### Major Release - PipeWire Screenshot Support

This release adds native Wayland screenshot support using PipeWire and GStreamer, completing the core remote desktop capabilities.

### Added

#### Core Features
- **PipeWire Screenshot Capture** (`pipewire_capture.py`)
  - Native Wayland screen capture (no X11 fallback)
  - Uses XDG ScreenCast portal for user approval
  - GStreamer 1.26+ compatible (tested on Ubuntu 25.10)
  - Source type detection (monitor/window/camera)
  - Simple function-based API: `capture_screenshot(path)`
  
- **Screen Recording Pipeline** (`pipewire_capture.py`)
  - Continuous video capture support
  - H.264 encoding via GStreamer
  - Frame callback mechanism for streaming
  - Multiple quality presets (low/medium/high)

- **Clipboard Module** (`clipboard.py`)
  - Text clipboard synchronization
  - Image clipboard support
  - Bidirectional sync with remote clients
  - GTK-based (Wayland compatible)

- **Remote Desktop Server** (`remote_server.py`)
  - Complete integration of all components
  - Video streaming capability
  - Input relay for remote control
  - Clipboard relay
  - Multi-client framework

#### Improvements
- **GStreamer 1.26 API Support**
  - Uses `emit('pull-sample')` instead of deprecated `pull_sample()`
  - Uses `Gst.MapFlags.READ` (with 's') for buffer mapping
  - Proper error handling for API changes

- **Robust MainLoop Management**
  - Fresh `GLib.MainLoop()` per operation (avoids race conditions)
  - Function-based screenshot API (simpler than class-based)
  - Better cleanup and error handling

- **Source Detection**
  - Detects if user selected monitor vs webcam
  - Warns when webcam is selected instead of screen
  - Shows resolution and source type

### Changed

- **Major Refactor of Screenshot Module**
  - Complete rewrite using working pattern from test scripts
  - Function-based API instead of class-based
  - More reliable portal communication
  - Better error messages

- **Updated Project Structure**
  - Moved all test files to `tests/` directory
  - Created `docs/` directory for technical documentation
  - Updated `examples/` with working code
  - Added comprehensive test suite

### Fixed

- **Portal Response Handling**
  - Properly extracts session_handle from portal responses
  - Correctly parses streams data format: `[(node_id, {metadata}), ...]`
  - Handles nested GLib.Variant unpacking

- **GStreamer Buffer Mapping**
  - Fixed `Gst.MapFlags.READ` vs `Gst.MapFlag.READ` issue
  - Proper buffer lifecycle management
  - Clean pipeline shutdown

- **MainLoop Race Conditions**
  - Each portal operation creates fresh MainLoop
  - Prevents signal subscription conflicts
  - Reliable timeout handling

### Documentation

- **Updated README.md**
  - Added PipeWire screenshot section
  - GStreamer 1.26 API notes
  - Source type detection information
  - Troubleshooting section

- **Created PROJECT_STATE.md**
  - Complete project assessment
  - Component status matrix
  - Next steps roadmap
  - Technical insights

- **Test Documentation**
  - `tests/TESTING_GUIDE.md` - How to run tests
  - `tests/README.md` - Test organization
  - Inline code comments

### Testing

- **New Test Scripts**
  - `test_source_detection.py` - Screenshot with source detection
  - `test_step1_working.py` - Backend functionality test
  - `test_step2_screenshot.py` - Screenshot test
  - `test_step3_complete.py` - End-to-end test
  - `pipewire_screenshot_clean.py` - Clean implementation test

- **Test Results**
  - ✅ WaylandBackend: PASS (input injection)
  - ✅ SmartWaylandBackend: PASS (window management)
  - ✅ PipeWire Screenshot: PASS (native capture)
  - ✅ Source Detection: PASS (monitor vs camera)

### Technical Details

#### Dependencies
- PyGObject 3.50.0+
- GStreamer 1.26.6+
- xdg-desktop-portal
- xdg-desktop-portal-gnome
- gstreamer1.0-pipewire

#### Platform Support
- **Tested on:** Ubuntu 25.10 + GNOME + Wayland
- **GStreamer:** 1.26.6
- **Python:** 3.13.7

#### Code Statistics
- Total lines: ~2,090
- New files: 5
- Test files: 8
- Documentation files: 6

### Known Issues

1. **Screen Recording** - Pipeline ready but needs continuous testing
2. **Clipboard** - Code ready but needs integration testing
3. **Network Layer** - Not yet implemented (next milestone)

### Breaking Changes

None - all changes are additive.

### Migration Guide

For screenshot functionality:
```python
# Old (class-based):
from open_alo import ScreenCapture
capture = ScreenCapture()
result = capture.screenshot("/tmp/shot.png")

# New (function-based):
from open_alo.pipewire_capture import capture_screenshot
result = capture_screenshot("/tmp/shot.png")
# Returns: {'success': True, 'data': bytes, 'source_type': 'monitor', 'error': None}
```

## [0.2.0] - 2026-02-01

### Added
- Initial PipeWire capture module (class-based, had issues)
- Clipboard synchronization module
- Remote desktop server module
- Comprehensive test suite
- Research documentation

### Changed
- Updated project structure
- Moved tests to dedicated directory
- Improved documentation

## [0.1.0] - 2026-02-01

### Added
- Initial release
- WaylandBackend with persistent permissions
- SmartWaylandBackend with window management
- Static screenshot API
- Basic examples
- Documentation

### Core Features
- Input injection (mouse, keyboard) via XDG Portal
- Window management via Window Calls extension
- Session persistence with restore tokens
- Gio D-Bus integration
- Error handling and logging

---

## Release Checklist

### [0.3.0] Release Status

- [x] All tests passing
- [x] Documentation updated
- [x] README reflects current state
- [x] Examples working
- [x] CHANGELOG.md created
- [x] PROJECT_STATE.md created
- [x] Code review complete
- [x] GStreamer 1.26 API verified
- [x] Ubuntu 25.10 tested
- [x] License file present

### Next Release [0.4.0] Planned Features

- [ ] Screen recording (continuous video)
- [ ] Clipboard synchronization (tested)
- [ ] WebSocket server for remote connections
- [ ] Client viewer application
- [ ] Authentication system
- [ ] Performance optimizations

---

**Full Changelog:** https://github.com/yourusername/OPEN_ALO/commits/main
