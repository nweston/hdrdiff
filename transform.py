"""Various operations on QTransforms.

All of these return a new transform.
"""
import qt


def fit(item_dims, view_dims):
    """Fit item_dims to view_dims, centering if aspect ratios differ."""

    scale = min(view / float(item) for item, view in zip(item_dims, view_dims))

    # Translate so center is at 0,0
    c1 = qt.QTransform.fromTranslate(*[-0.5 * i for i in item_dims])
    # Scale to fit
    s = qt.QTransform.fromScale(scale, scale)
    # Translate item center back to view center
    c2 = qt.QTransform.fromTranslate(*[0.5 * i for i in view_dims])

    return c1 * s * c2


def zoom_to_scale(zoom_level):
    """Convert a zoom level to a scale factor.

    Positive zoom levels zoom in (with integer levels translating to 2x,
    3x, etc), and negative zoom levels zoom out (integer levels translate
    to 1/2, 1/3, 1/4, etc).
    """
    if zoom_level > 0:
        return zoom_level + 1
    else:
        return 1 / float(-1 * zoom_level + 1)


def scale_to_zoom(scale_factor):
    """Convert a scale factor to a zoom level."""
    if scale_factor > 1.0:
        return scale_factor - 1
    else:
        return -1 * (1.0 / scale_factor - 1)


def scale_factor(xform):
    """Get the scale of a QTransform, assuming uniform scaling."""
    assert xform.m11() == xform.m22(), "Scale must be uniform"
    return xform.m11()


def zoom(xform, view_dims, increment):
    """Adjust zoom level relative to the current scale."""
    center = [i * 0.5 for i in view_dims]
    old_scale = scale_factor(xform)
    new_scale = zoom_to_scale(scale_to_zoom(old_scale) + increment)
    relative_scale = new_scale / old_scale

    # Translate view_center to 0, 0
    c1 = qt.QTransform.fromTranslate(*[-1 * i for i in center])
    # Scale to fit
    s = qt.QTransform.fromScale(relative_scale, relative_scale)
    # Translate back to view center
    c2 = qt.QTransform.fromTranslate(*center)

    return xform * c1 * s * c2
