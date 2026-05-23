"""
Unit tests for open_alo_core exception hierarchy.
"""

import pytest
from open_alo_core import (
    CoreError,
    PermissionDenied,
    CaptureError,
    InputError,
    SessionError,
    BackendNotAvailable,
)


class TestExceptionHierarchy:
    """All custom exceptions must inherit from CoreError."""

    @pytest.mark.parametrize(
        "exc_cls",
        [
            PermissionDenied,
            CaptureError,
            InputError,
            SessionError,
            BackendNotAvailable,
        ],
    )
    def test_inherits_from_core_error(self, exc_cls):
        assert issubclass(exc_cls, CoreError)

    def test_core_error_inherits_from_exception(self):
        assert issubclass(CoreError, Exception)


class TestExceptionInstances:
    """Exceptions can be raised and carry messages."""

    def test_permission_denied_message(self):
        with pytest.raises(PermissionDenied, match="permission"):
            raise PermissionDenied("User denied permission")

    def test_capture_error_message(self):
        with pytest.raises(CaptureError, match="capture"):
            raise CaptureError("Screen capture failed")

    def test_input_error_message(self):
        with pytest.raises(InputError, match="Click"):
            raise InputError("Click failed: timeout")

    def test_session_error_message(self):
        with pytest.raises(SessionError, match="session"):
            raise SessionError("Failed to create session")

    def test_backend_not_available_message(self):
        with pytest.raises(BackendNotAvailable, match="backend"):
            raise BackendNotAvailable("Requested backend not available")

    def test_exception_chaining(self):
        """Ensure proper exception chaining via 'from e'."""
        try:
            try:
                raise ValueError("original error")
            except ValueError as e:
                raise InputError("Input failed") from e
        except InputError as e:
            assert isinstance(e.__cause__, ValueError)
            assert str(e.__cause__) == "original error"
