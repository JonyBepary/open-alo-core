"""
Verify all public API symbols can be imported and __all__ is correct.
"""

from open_alo_core import (  # noqa: F401
    # Main controllers
    WaylandInput,
    WaylandCapture,
    UnifiedRemoteDesktop,
    # Window management
    WindowManager,
    WindowInfo,
    WindowType,
    FrameType,
    get_focused_window,
    find_window,
    list_windows,
    activate_window,
    # Types
    Point,
    Size,
    Rect,
    # Constants
    BUTTON_LEFT,
    BUTTON_MIDDLE,
    BUTTON_RIGHT,
    # Exceptions
    CoreError,
    PermissionDenied,
    CaptureError,
    InputError,
    SessionError,
    BackendNotAvailable,
    # Utilities
    detect_session_type,
    is_wayland,
    is_portal_available,
    is_pipewire_available,
    # Key normalization
    normalize_key,
)


def test_version_string():
    from open_alo_core import __version__

    parts = __version__.split(".")
    assert len(parts) == 3
    major, minor, patch = parts
    assert major.isdigit()
    assert minor.isdigit()
    assert patch.isdigit()


def test_all_exports_match():
    """Every name in __all__ should be importable at module level."""
    import open_alo_core

    for name in open_alo_core.__all__:
        assert hasattr(
            open_alo_core, name
        ), f"{name} is in __all__ but not accessible as open_alo_core.{name}"
