"""Utilities for QTransforms."""
import qt


def fit(item_dims, view_dims):
    scale = min(view / float(item) for item, view in zip(item_dims, view_dims))

    # Translate so center is at 0,0
    c1 = qt.QTransform.fromTranslate(*[-0.5 * i for i in item_dims])
    # Scale to fit
    s = qt.QTransform.fromScale(scale, scale)
    # Translate item center back to view center
    c2 = qt.QTransform.fromTranslate(*[0.5 * i for i in view_dims])

    return c1 * s * c2
