"""
Verify all public API symbols can be imported and __all__ is correct.
"""

from open_alo_core import (  # noqa: F401; Main controllers; Window management; Types; Constants; Exceptions; Utilities; Key normalization
    BUTTON_LEFT,
    BUTTON_MIDDLE,
    BUTTON_RIGHT,
    BackendNotAvailable,
    CaptureError,
    CoreError,
    FrameType,
    InputError,
    PermissionDenied,
    Point,
    Rect,
    SessionError,
    Size,
    UnifiedRemoteDesktop,
    WaylandCapture,
    WaylandInput,
    WindowInfo,
    WindowManager,
    WindowType,
    activate_window,
    create_unified_desktop,
    detect_session_type,
    find_window,
    get_focused_window,
    is_pipewire_available,
    is_portal_available,
    is_wayland,
    list_windows,
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

