"""
Unit tests for open_alo_core.geometry and open_alo_core.calibration (M1/M3 Promotions)
"""

import pytest
from open_alo_core import (
    Point,
    Rect,
    AffineTransform2D,
    solve_affine,
    residual,
    RESIDUAL_LIMIT_PX,
)


class TestAffineTransform2D:
    def test_identity_transform(self):
        t = AffineTransform2D()
        pt = Point(100, 200)
        rect = Rect(50, 60, 120, 80)
        assert t.transform_point(pt) == pt
        assert t.transform_rect(rect) == rect
        assert t.inverse_point(pt) == pt
        assert t.inverse_rect(rect) == rect

    def test_scale_and_offset_transform(self):
        # 2x scale with offset (10, 20)
        t = AffineTransform2D(scale_x=2.0, scale_y=2.0, offset_x=10.0, offset_y=20.0)
        pt = Point(100, 200)
        transformed_pt = t.transform_point(pt)
        assert transformed_pt == Point(210, 420)
        assert t.inverse_point(transformed_pt) == pt

        rect = Rect(10, 15, 30, 40)
        transformed_rect = t.transform_rect(rect)
        assert transformed_rect == Rect(30, 50, 60, 80)
        assert t.inverse_rect(transformed_rect) == rect

    def test_zero_scale_inverse_raises(self):
        t = AffineTransform2D(scale_x=0.0, scale_y=2.0)
        with pytest.raises(ValueError, match="Cannot invert"):
            t.inverse_point(Point(10, 10))
        with pytest.raises(ValueError, match="Cannot invert"):
            t.inverse_rect(Rect(10, 10, 20, 20))


class TestCalibrationSolvers:
    def test_solve_affine_exact(self):
        # AT-SPI at (0, 0, 927, 524) vs Mutter at (66, 40, 1854, 1048) -> 2.0x scale
        atspi = Rect(0, 0, 927, 524)
        mutter = Rect(66, 40, 1854, 1048)

        t = solve_affine(mutter, atspi)
        assert t.scale_x == 2.0
        assert t.scale_y == 2.0
        assert t.offset_x == 66.0
        assert t.offset_y == 40.0

        res = residual(mutter, atspi, t)
        assert res <= RESIDUAL_LIMIT_PX
        assert res == 0.0

    def test_solve_affine_invalid_extents_raises(self):
        with pytest.raises(ValueError, match="Invalid AT-SPI extents"):
            solve_affine(Rect(0, 0, 100, 100), Rect(0, 0, 0, 100))
