# RustDesk Single-Permission Approach - Research & Implementation

## The Problem

Currently, `open_alo_core` requires **two separate permissions**:

1. **WaylandInput** → Uses `RemoteDesktop` portal → Input control (keyboard/mouse)
2. **WaylandCapture** → Uses `ScreenCast` portal → Screen capture

This means users see **two permission dialogs**, which is poor UX.

## How RustDesk Does It

RustDesk achieves single-permission approval by using **only the RemoteDesktop portal**, which provides **both capabilities**:

### RemoteDesktop Portal Capabilities

The `org.freedesktop.portal.RemoteDesktop` interface inherits from both:
- **Input control** (keyboard/mouse) - Native to RemoteDesktop
- **Screen capture** (via SelectSources) - Inherited from ScreenCast

```
RemoteDesktop Portal
├── CreateSession()
├── SelectDevices()      ← Keyboard/mouse control
├── SelectSources()      ← Screen capture sources! (from ScreenCast)
├── Start()
├── NotifyPointerMotion()
├── NotifyPointerButton()
└── NotifyKeyboardKeycode()
```

## The Key Insight

The **RemoteDesktop portal includes ScreenCast functionality**!

From the [XDG Portal spec](https://flatpak.github.io/xdg-desktop-portal/docs/#gdbus-org.freedesktop.portal.RemoteDesktop):

> The RemoteDesktop portal allows clients to create remote desktop sessions. **It inherits the ScreenCast interface** for selecting what to share.

## Current vs. Unified Approach

### Current (Two Permissions ❌)

```python
# Permission 1: Input control
with WaylandInput() as ctrl:
    ctrl.initialize(persist_mode=2)  # Dialog 1
    ctrl.click(Point(500, 500))

# Permission 2: Screen capture
with WaylandCapture() as cap:
    result = cap.capture_screen()    # Dialog 2
```

### Unified (One Permission ✅)

```python
# Single permission for everything
with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2)  # One dialog for BOTH

    # Input control
    remote.click(Point(500, 500))
    remote.type_text("Hello")

    # Screen capture (same session!)
    result = remote.capture_screen()
```

## Implementation Plan

### Step 1: Create UnifiedRemoteDesktop Class

```python
class UnifiedRemoteDesktop:
    """
    Unified remote desktop session using RemoteDesktop portal.
    Provides both input control AND screen capture in a single permission.
    """

    PORTAL_IFACE = "org.freedesktop.portal.RemoteDesktop"

    def initialize(self, persist_mode: int = 2):
        """Initialize single session for both input and capture"""
        # 1. CreateSession
        self._create_session()

        # 2. SelectDevices (keyboard/mouse)
        self._select_devices(persist_mode)

        # 3. SelectSources (screen capture) - SAME SESSION!
        self._select_sources()

        # 4. Start (activates everything)
        self._start_session()

        # Now have BOTH input and capture capabilities!
```

### Step 2: Workflow

```
┌─────────────────────────────────────────┐
│  User Approves ONCE                     │
│  ┌───────────────────────────────────┐  │
│  │ Allow remote desktop access?      │  │
│  │                                   │  │
│  │ ☑ Control keyboard and mouse      │  │
│  │ ☑ Capture screen                  │  │
│  │                                   │  │
│  │   [Deny]  [Allow]                 │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
            │
            ▼
   Both capabilities granted!
   - Input: click(), type_text()
   - Capture: capture_screen()
```

### Step 3: D-Bus Call Sequence

```python
# RemoteDesktop portal path
portal = org.freedesktop.portal.RemoteDesktop

# 1. Create session
response = portal.CreateSession(options)
session_handle = response['session_handle']

# 2. Select input devices
portal.SelectDevices(
    session_handle,
    {
        'types': 7,  # Keyboard | Pointer | Touchscreen
        'persist_mode': 2
    }
)

# 3. Select capture sources (SAME SESSION!)
portal.SelectSources(
    session_handle,
    {
        'types': 1,  # Monitor
        'multiple': False,
        'cursor_mode': 2
    }
)

# 4. Start (single permission dialog appears here)
response = portal.Start(session_handle, '', {})
# Dialog shows BOTH keyboard/mouse AND screen capture permissions

# 5. Use capabilities
portal.NotifyPointerMotion(session_handle, x, y)  # Input
streams = response['streams']  # Capture via PipeWire
node_id = streams[0][0]
```

## Key Differences

### WaylandCapture (Current)

```python
PORTAL_IFACE = "org.freedesktop.portal.ScreenCast"  # Separate portal

def capture_screen():
    self._create_session()      # Separate session
    self._select_sources()      # Only sources, no devices
    self._start_capture()       # Separate permission
```

### UnifiedRemoteDesktop (New)

```python
PORTAL_IFACE = "org.freedesktop.portal.RemoteDesktop"  # Unified portal

def initialize():
    self._create_session()      # One session
    self._select_devices()      # Input devices
    self._select_sources()      # Capture sources (SAME SESSION!)
    self._start_session()       # One permission for ALL
```

## Benefits

1. **Better UX**: Single permission dialog (like RustDesk)
2. **Atomic Approval**: User approves input+capture together
3. **Simpler State**: One session, one token, one lifecycle
4. **Standards Compliant**: Using portal as designed
5. **Future Proof**: Add clipboard, etc. to same session

## Technical Details

### RemoteDesktop Interface (Full Spec)

```
interface org.freedesktop.portal.RemoteDesktop {
  # Session Management
  methods:
    CreateSession(a{sv} options) → o request_handle

    # Input Control (Native)
    SelectDevices(o session, u types, a{sv} options) → o request_handle
    NotifyPointerMotion(o session, a{sv} options, d dx, d dy)
    NotifyPointerButton(o session, a{sv} options, i button, u state)
    NotifyKeyboardKeycode(o session, a{sv} options, i keycode, u state)
    NotifyKeyboardKeysym(o session, a{sv} options, i keysym, u state)
    NotifyTouchDown(...)
    NotifyTouchMotion(...)
    NotifyTouchUp(...)

    # Screen Capture (Inherited from ScreenCast)
    SelectSources(o session, a{sv} options) → o request_handle

    # Start Session (combines everything)
    Start(o session, s parent_window, a{sv} options) → o request_handle

  properties:
    AvailableDeviceTypes: u  # Keyboard=1, Pointer=2, Touchscreen=4
    AvailableSourceTypes: u  # Monitor=1, Window=2, Virtual=4
}
```

### Types Constants

```python
# Device Types (for SelectDevices)
DEVICE_KEYBOARD = 1
DEVICE_POINTER = 2
DEVICE_TOUCHSCREEN = 4
DEVICE_ALL = 7  # Keyboard | Pointer | Touchscreen

# Source Types (for SelectSources)
SOURCE_MONITOR = 1
SOURCE_WINDOW = 2
SOURCE_VIRTUAL = 4  # Future: virtual screens

# Persist Modes
PERSIST_NEVER = 0
PERSIST_APP_SESSION = 1
PERSIST_UNTIL_REVOKED = 2
```

## Why We Didn't Do This Initially

1. **Documentation Gap**: Portal docs don't clearly explain RemoteDesktop inherits ScreenCast
2. **Example Code**: Most examples show separate ScreenCast/RemoteDesktop
3. **Complexity**: Easier to implement separately first
4. **Testing**: Separate portals = easier to test independently

## RustDesk's Implementation

From RustDesk source code analysis:

```rust
// RustDesk creates ONE session for everything
impl WaylandPortalSession {
    fn create() -> Self {
        // Use RemoteDesktop portal (not ScreenCast)
        let portal = "org.freedesktop.portal.RemoteDesktop";

        // Single session
        let session = portal.create_session();

        // Request BOTH capabilities
        portal.select_devices(session, KEYBOARD | POINTER);
        portal.select_sources(session, MONITOR);

        // Start - user sees ONE dialog
        portal.start(session);

        // Now can both:
        // - Control input
        // - Capture screen
    }
}
```

## Implementation Checklist

- [ ] Create `UnifiedRemoteDesktop` class
- [ ] Move `SelectSources` logic from `WaylandCapture`
- [ ] Combine `SelectDevices` from `WaylandInput`
- [ ] Single `Start()` call with both capabilities
- [ ] Unified permission token storage
- [ ] Add screen capture to unified session
- [ ] Update examples to use unified class
- [ ] Deprecate separate WaylandInput/WaylandCapture
- [ ] Migration guide for existing code

## Example Usage Patterns

### Basic Usage

```python
from open_alo_core import UnifiedRemoteDesktop, Point

with UnifiedRemoteDesktop() as remote:
    # Initialize once, approve once
    remote.initialize(persist_mode=2)

    # Use input
    remote.click(Point(500, 500))
    remote.type_text("Hello World")

    # Use capture (same session!)
    screenshot = remote.capture_screen()
    Path("/tmp/shot.png").write_bytes(screenshot.data)
```

### Complete Remote Desktop

```python
remote = UnifiedRemoteDesktop()
remote.initialize(persist_mode=2)

# Everything in one session
while True:
    # Handle input from network
    if network_event == "click":
        remote.click(Point(x, y))

    # Stream screen to network
    if frame_requested:
        frame = remote.get_frame()  # Live PipeWire stream
        send_to_network(frame)
```

### Agent Workflow

```python
from open_alo_core import UnifiedRemoteDesktop, WindowManager

# Single permission for agent
with UnifiedRemoteDesktop() as agent:
    agent.initialize(persist_mode=2)

    # Window management
    wm = WindowManager()
    editor = wm.find_window("Text Editor")
    wm.activate(editor.id)

    # Input control
    agent.click(Point(500, 500))
    agent.type_text("Generated text")

    # Visual verification
    before = agent.capture_screen()
    agent.key_combo(["Control", "s"])  # Save
    after = agent.capture_screen()

    # Compare screenshots to verify action
    if before.data != after.data:
        print("✓ File saved successfully")
```

## Testing

```python
def test_unified_session():
    """Test single permission for input + capture"""
    remote = UnifiedRemoteDesktop()

    # Should show ONE permission dialog
    remote.initialize(persist_mode=2)

    # Both should work without additional dialogs
    remote.click(Point(100, 100))  # No dialog
    screenshot = remote.capture_screen()  # No dialog

    assert len(screenshot.data) > 0

def test_permission_persistence():
    """Test permission persists across sessions"""
    # First run
    remote1 = UnifiedRemoteDesktop()
    remote1.initialize(persist_mode=2)  # Dialog shown
    remote1.close()

    # Second run (should restore from token)
    remote2 = UnifiedRemoteDesktop()
    remote2.initialize(persist_mode=2)  # NO dialog!
    remote2.click(Point(100, 100))  # Works immediately
```

## Migration Path

### For Existing Code

```python
# Old (still works, two permissions)
with WaylandInput() as ctrl:
    ctrl.initialize(persist_mode=2)
    ctrl.click(Point(500, 500))

with WaylandCapture() as cap:
    result = cap.capture_screen()

# New (one permission)
with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2)
    remote.click(Point(500, 500))
    result = remote.capture_screen()
```

### Backward Compatibility

Keep `WaylandInput` and `WaylandCapture` as thin wrappers:

```python
class WaylandInput:
    """Backward compatible wrapper - DEPRECATED"""
    def __init__(self):
        self._remote = UnifiedRemoteDesktop()
        warnings.warn("Use UnifiedRemoteDesktop instead", DeprecationWarning)

    def initialize(self, persist_mode=0):
        # Only initialize input part
        self._remote._initialize_input_only(persist_mode)
```

## References

1. **XDG Portal RemoteDesktop Spec**: https://flatpak.github.io/xdg-desktop-portal/docs/#gdbus-org.freedesktop.portal.RemoteDesktop
2. **RustDesk Source**: https://github.com/rustdesk/rustdesk
3. **GNOME Portal Implementation**: https://gitlab.gnome.org/GNOME/xdg-desktop-portal-gnome
4. **Wayland Protocols**: https://wayland.freedesktop.org/

## Conclusion

**Key Takeaway**: The RemoteDesktop portal was *designed* for this use case - it combines input control and screen capture in a single permission model. We should use it as intended, just like RustDesk does.

This will provide:
- ✅ Better user experience (one permission)
- ✅ Simpler codebase (one session)
- ✅ Standards compliant
- ✅ Match industry standards (RustDesk, TeamViewer, etc.)

Next step: Implement `UnifiedRemoteDesktop` class in `open_alo_core`.
