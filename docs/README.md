# Documentation

Documentation for **open_alo_core** - Modern Linux desktop automation SDK.

## 📚 Core Documentation

### [UNIFIED_QUICK_REFERENCE.md](UNIFIED_QUICK_REFERENCE.md) ⭐
**Start here!** Quick reference for common patterns and API usage.
- Import examples
- Basic usage
- All API methods
- Common patterns
- Troubleshooting

### [API Reference](../open_alo_core/API_REFERENCE.md)
Complete API documentation for all classes and methods:
- `UnifiedRemoteDesktop` (recommended)
- `WaylandInput`, `WaylandCapture` (legacy)
- `WindowManager`
- Types (`Point`, `Size`, `Rect`, `WindowInfo`)
- Exceptions
- Utilities

### [MIGRATION_TO_UNIFIED.md](MIGRATION_TO_UNIFIED.md)
Migration guide from legacy two-permission API to unified approach:
- Side-by-side comparisons
- Step-by-step migration
- Code examples
- FAQ

## 🔧 Technical Documentation

### [UNIFIED_REMOTEDESKTOP_APPROACH.md](UNIFIED_REMOTEDESKTOP_APPROACH.md)
Technical details of the RustDesk-style single-permission implementation:
- How RemoteDesktop portal works
- Why it's better than separate portals
- Portal call sequence
- D-Bus interface details

### [UNIFIED_REMOTEDESKTOP_SUMMARY.md](UNIFIED_REMOTEDESKTOP_SUMMARY.md)
Implementation summary and test results:
- What was built
- Architecture overview
- API comparison
- Performance metrics
- Use cases

### [WINDOW_MANAGEMENT_API.md](WINDOW_MANAGEMENT_API.md)
Window management documentation:
- WindowManager class
- Window Calls GNOME extension
- Finding and activating windows
- Window operations (maximize, minimize, move, resize)
- Workspace management

## 📖 Additional Resources

### Examples
See [examples/README.md](../examples/README.md) for working code examples:
- `unified_minimal.py` - Quick start
- `unified_ai_agent_demo.py` - Full workflow
- `window_management_demo.py` - Window control

### Tests
See [tests/README.md](../tests/README.md) for test suite documentation.

### Archive
Historical documentation moved to [archive/docs/](../archive/docs/):
- Old architecture diagrams
- Early research notes
- Historical test results
- Development timeline

---

## Quick Links

**Getting Started:**
1. [Quick Reference](UNIFIED_QUICK_REFERENCE.md) - Common patterns
2. [Examples](../examples/README.md) - Working code
3. [API Reference](../open_alo_core/API_REFERENCE.md) - Complete API

**Technical Details:**
- [Implementation Approach](UNIFIED_REMOTEDESKTOP_APPROACH.md)
- [Implementation Summary](UNIFIED_REMOTEDESKTOP_SUMMARY.md)
- [Window Management](WINDOW_MANAGEMENT_API.md)

**Migration:**
- [Migration Guide](MIGRATION_TO_UNIFIED.md) - Upgrade from legacy API

---

**Last Updated:** February 3, 2026
**Version:** open_alo_core v0.1.0
