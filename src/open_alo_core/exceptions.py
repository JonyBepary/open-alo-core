"""
Exception hierarchy for open_alo_core

All exceptions inherit from CoreError for easy catching.
"""


class CoreError(Exception):
    """Base exception for all core errors"""
    pass


class PermissionDenied(CoreError):
    """User denied portal permission or insufficient privileges"""
    pass


class CaptureError(CoreError):
    """Screen capture failed"""
    pass


class InputError(CoreError):
    """Input injection failed"""
    pass


class SessionError(CoreError):
    """Portal session creation/management failed"""
    pass


class BackendNotAvailable(CoreError):
    """Requested backend not available on this system"""
    pass
