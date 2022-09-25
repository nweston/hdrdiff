"""Better layout classes for Qt.

These provide several conveniences:

    1. Constructor takes margin as a keyword argument so it can easily be
       changed.

    2. Margin defaults to zero to prevent ever-increasing padding as
       layouts are nested.

    3. Constructor takes children as a keyword argument. This is a list of
       QWidgets and QLayouts, all of which will be added with the
       appropriate method calls.

    The combination of these features can condense many lines of
    addLayout/addWidget/setMargin calls into a few nested calls, with a
    structure that visually reflects the layout.
"""

import qt


class Stretch:
    def __init__(self, stretch):
        self.stretch = stretch


class EasyLayout:
    """Base class for layout helpers."""

    def _setup(self, margin, children):
        """Set up layout by setting margin and adding all children.

        Children may be QWidgets or QLayouts."""

        self.setMargin(margin)
        for c in children:
            if isinstance(c, qt.QWidget):
                self.addWidget(c)
            elif isinstance(c, int):
                self.addSpacing(c)
            elif isinstance(c, Stretch):
                self.addStretch(c.stretch)
            else:
                self.addLayout(c)


class HBox(qt.QHBoxLayout, EasyLayout):
    """Convenience wrapper for QHBoxLayout."""

    def __init__(self, parent=None, margin=0, children=[], **kwargs):
        """Initialize layout, set margin and adding children."""
        super().__init__(parent)
        self._setup(margin, children)


class VBox(qt.QVBoxLayout, EasyLayout):
    """Convenience wrapper for QVBoxLayout."""

    def __init__(self, parent=None, margin=0, children=[], **kwargs):
        """Initialize layout, set margin and adding children."""
        super().__init__(parent)
        self._setup(margin, children)
