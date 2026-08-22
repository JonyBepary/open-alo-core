"""
Unit tests for open_alo_core.preflight: GeometricPreflight
"""

import pytest

from open_alo_core import GeometricPreflight, Point, Rect


class TestGeometricPreflight:
    """Test pure geometric preflight validation"""

    def test_verify_point_bounds_valid(self):
        pf = GeometricPreflight(stream_size=(1920, 1080))
        verdict = pf.verify_point_bounds(Point(500, 400))
        assert verdict.is_safe is True

    def test_verify_point_bounds_out_of_bounds(self):
        pf = GeometricPreflight(stream_size=(1920, 1080))
        verdict = pf.verify_point_bounds(Point(2500, 400))
        assert verdict.is_safe is False
        assert "failed sentinel/bounds validation" in verdict.reason

    def test_verify_point_bounds_negative_sentinel(self):
        pf = GeometricPreflight(stream_size=(1920, 1080))
        verdict = pf.verify_point_bounds(Point(-2147483648, 100))
        assert verdict.is_safe is False

    def test_verify_point_occlusion_not_occluded(self):
        pf = GeometricPreflight()
        win_rects = {
            1: Rect(100, 100, 800, 600),
            2: Rect(1000, 100, 800, 600),
        }
        z_order = [1, 2]
        # Point on window 1 at (200, 200) is NOT covered by window 2 at (1000, 100)
        verdict = pf.verify_point_occlusion(Point(200, 200), 1, win_rects, z_order)
        assert verdict.is_safe is True
        assert pf.is_point_occluded(Point(200, 200), 1, win_rects, z_order) is False

    def test_verify_point_occlusion_covered_by_higher_window(self):
        pf = GeometricPreflight()
        win_rects = {
            1: Rect(100, 100, 800, 600),  # lower window
            2: Rect(150, 150, 400, 400),  # higher window overlapping
        }
        z_order = [1, 2]
        # Point at (200, 200) on window 1 is covered by window 2
        verdict = pf.verify_point_occlusion(Point(200, 200), 1, win_rects, z_order)
        assert verdict.is_safe is False
        assert "is occluded by higher window" in verdict.reason
        assert pf.is_point_occluded(Point(200, 200), 1, win_rects, z_order) is True

    def test_verify_point_occlusion_top_window_never_occluded(self):
        pf = GeometricPreflight()
        win_rects = {
            1: Rect(100, 100, 800, 600),
            2: Rect(150, 150, 400, 400),
        }
        z_order = [1, 2]
        # Window 2 is on top, point on window 2 cannot be occluded
        verdict = pf.verify_point_occlusion(Point(200, 200), 2, win_rects, z_order)
        assert verdict.is_safe is True
