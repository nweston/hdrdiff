import unittest
import qt
from transform import fit


def do_fit(item, scene):
    rect = fit(item, scene).mapRect(qt.QRectF(0, 0, *item))
    xformed_rect = (rect.left(), rect.top(), rect.right(), rect.bottom())
    scene_rect = (0, 0, *scene)
    return xformed_rect, scene_rect


def centered(small_rect, big_rect):
    """Return small_rect, translated to be centered in big_rect."""

    sx0, sy0, sx1, sy1 = small_rect
    bx0, by0, bx1, by1 = big_rect

    sw = sx1 - sx0
    sh = sy1 - sy0
    bw = bx1 - bx0
    bh = by1 - by0

    assert sw == bw or sh == bh

    if sw < bw:
        margin = (bw - sw) * 0.5
        return margin, sy0, bw - margin, sy1
    else:
        margin = (bh - sh) * 0.5
        return sx0, margin, sx1, bh - margin


class TestFit(unittest.TestCase):
    def test_zoom_in_simple(self):
        xformed, scene = do_fit((100, 50), (250, 125))
        self.assertEqual(xformed, scene)

    def test_zoom_in_xmargin(self):
        xformed, scene = do_fit((50, 50), (250, 125))
        self.assertEqual(xformed, centered(xformed, scene))

    def test_zoom_in_ymargin(self):
        xformed, scene = do_fit((100, 25), (250, 125))
        self.assertEqual(xformed, centered(xformed, scene))

    def test_zoom_out_simple(self):
        xformed, scene = do_fit((250, 125), (100, 50))
        self.assertEqual(xformed, scene)

    def test_zoom_out_xmargin(self):
        xformed, scene = do_fit((200, 125), (100, 50))
        self.assertEqual(xformed, centered(xformed, scene))

    def test_zoom_out_ymargin(self):
        xformed, scene = do_fit((250, 100), (100, 50))
        self.assertEqual(xformed, centered(xformed, scene))
