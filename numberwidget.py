import qt

# FIXME: should contain a QLineEdit instead of subclassing it, to
# prevent direct text manipulation from outside the class.


class NumberWidget(qt.QLineEdit):
    """A widget for entering numbers.

    Adjust values by dragging, or click the text to type a value."""

    valueChanged = qt.Signal(float)
    STEP = 0.005
    DECIMALS = 3

    def __init__(self, start_value, min_value=None, parent=None, **args):
        super().__init__(parent, **args)
        self.setValidator(qt.QDoubleValidator())
        self.setAlignment(qt.Qt.AlignCenter)
        self.setMouseTracking(True)

        self.setReadOnly(True)
        self.setCursor(qt.Qt.CursorShape.SizeHorCursor)
        self.editingFinished.connect(self._finish_edit)

        self._drag_state = None
        self._min = min_value
        self._value = start_value
        self.setText(f"{self._value:g}")

    @property
    def value(self):
        return self._value

    def set_value(self, value):
        value = round(value, self.DECIMALS)
        if self._min is not None:
            self._value = max(self._min, value)
        else:
            self._value = value
        self.setText(f"{self._value:g}")
        self.valueChanged.emit(self._value)

    def mouseMoveEvent(self, evt):
        if self._drag_state is not None:
            x0, v0 = self._drag_state
            self.set_value(v0 + (evt.x() - x0) * self.STEP)

        elif evt.buttons() == qt.Qt.LeftButton:
            self._drag_state = (evt.x(), self._value)

    def mouseReleaseEvent(self, evt):
        if self._drag_state is None:
            self.setReadOnly(False)
            self.setCursor(qt.Qt.CursorShape.IBeamCursor)
            self.setSelection(0, len(self.text()))
        self._drag_state = None

    def _finish_edit(self):
        self.setCursor(qt.Qt.CursorShape.SizeHorCursor)
        self.set_value(float(self.text()))

        self.setReadOnly(True)
        self.setCursor(qt.Qt.CursorShape.SizeHorCursor)
