import unittest
import qt
from transform import fit, scale_factor, zoom


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


def center(rect):
    if isinstance(rect, qt.QRectF):
        return rect.center().x(), rect.center().y()
    else:
        x0, y0, x1, y1 = rect
        return (x1 - x0) * 0.5, (y1 - y0) * 0.5


def map_inv(xform, *args):
    inverse, _ = xform.inverted()
    return inverse.map(*args)


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


class TestZoom(unittest.TestCase):
    def test_scale_factor(self):
        xform = qt.QTransform()
        self.assertEqual(scale_factor(xform), 1.0)
        self.assertEqual(scale_factor(zoom(xform, (0, 0), 0.5)), 1.5)
        self.assertEqual(scale_factor(zoom(xform, (0, 0), 1)), 2)
        self.assertEqual(scale_factor(zoom(xform, (0, 0), -1)), 0.5)
        self.assertEqual(scale_factor(zoom(xform, (0, 0), -3)), 0.25)

    def test_center(self):
        item = (100, 50)
        item_qrect = qt.QRectF(0, 0, *item)
        view = (250, 125)
        view_center = tuple(0.5 * i for i in view)
        xform = fit(item, view)
        self.assertEqual(center(xform.mapRect(item_qrect)), view_center)

        # If the image is centered, it should stay centered
        self.assertEqual(
            center(zoom(xform, view_center, 0.5).mapRect(item_qrect)), view_center
        )
        self.assertEqual(
            center(zoom(xform, view_center, 2).mapRect(item_qrect)), view_center
        )
        self.assertEqual(
            center(zoom(xform, view_center, -1).mapRect(item_qrect)), view_center
        )
        self.assertEqual(
            center(zoom(xform, view_center, -3).mapRect(item_qrect)), view_center
        )

        # If the image is not centered, then whatever point is at the
        # center of the view should stay there, but the center of the
        # image itself will change.
        xform2 = xform * qt.QTransform.fromTranslate(10, 20)
        current_center = map_inv(xform2, *view_center)

        self.assertEqual(
            map_inv(zoom(xform2, view_center, 0.5), *view_center), current_center
        )
        self.assertEqual(
            map_inv(zoom(xform2, view_center, 2), *view_center), current_center
        )
        self.assertEqual(
            map_inv(zoom(xform2, view_center, -1), *view_center), current_center
        )
        self.assertEqual(
            map_inv(zoom(xform2, view_center, -3), *view_center), current_center
        )
