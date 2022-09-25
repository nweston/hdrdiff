import enable_exr  # noqa: F401
import cv2
import sys
import qt
import numpy
import transform
from layout import HBox, VBox


def dims(obj):
    """Return (width, height) tuple for object with width() and height() methods."""
    return obj.width(), obj.height()


class ImageView(qt.QGraphicsView):
    def __init__(self, image, parent=None, **kwargs):
        scene = qt.QGraphicsScene()
        self._image = image
        self._item = qt.QGraphicsPixmapItem(qt.QPixmap.fromImage(image))
        scene.addItem(self._item)

        super().__init__(scene=scene, parent=parent, **kwargs)
        self.setBackgroundBrush(qt.Qt.gray)
        self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)

        self._drag_state = None

    @property
    def _transform(self):
        return self._item.transform()

    @_transform.setter
    def _transform(self, t):
        self._item.setTransform(t)

    def resizeEvent(self, evt):
        super().resizeEvent(evt)

        if evt.spontaneous():
            return

        self.setSceneRect(0, 0, self.width(), self.height())
        self.reset_view()

    def wheelEvent(self, evt):
        # Delta of one wheel click is usually 120
        self._transform = transform.zoom(
            self._transform,
            center=(evt.x(), evt.y()),
            increment=evt.angleDelta().y() / 240.0,
        )

    def mouseMoveEvent(self, evt):
        if evt.buttons() == qt.Qt.LeftButton:
            if self._drag_state is None:
                self._drag_state = (self._transform, (evt.x(), evt.y()))
                self.setCursor(qt.Qt.CursorShape.ClosedHandCursor)
            else:
                self._transform = transform.pan(*self._drag_state, (evt.x(), evt.y()))

    def mouseReleaseEvent(self, evt):
        self._drag_state = None
        self.setCursor(qt.Qt.CursorShape.ArrowCursor)

    def reset_view(self):
        self._transform = transform.fit(dims(self._image), dims(self.sceneRect()))

    def zoom_in(self):
        self._transform = transform.zoom(
            self._transform,
            tuple(0.5 * i for i in dims(self.sceneRect())),
            increment=0.5,
        )

    def zoom_out(self):
        self._transform = transform.zoom(
            self._transform,
            tuple(0.5 * i for i in dims(self.sceneRect())),
            increment=-0.5,
        )


if __name__ == "__main__":
    img = cv2.imread(sys.argv[1], cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)

    # Convert to 8-bit and add alpha channel to match QImage format
    height, width = img.shape[:2]
    bits = cv2.cvtColor(
        (numpy.clip(img, 0, 1) * 255).astype(numpy.uint8), cv2.COLOR_BGR2BGRA
    ).tobytes()
    qimage = qt.QImage(bits, width, height, width * 4, qt.QImage.Format_RGB32)

    app = qt.QApplication([])
    window = qt.QWidget()
    view = ImageView(qimage, parent=window)
    info = qt.QLabel(parent=window)
    HBox(window, margin=8, children=[view, VBox(children=[info])])

    # Shortcuts
    shortcuts = [
        (
            "Zoom In",
            view.zoom_in,
            [qt.Qt.CTRL + qt.Qt.Key_Equal, qt.Qt.CTRL + qt.Qt.Key_Plus],
        ),
        ("Zoom Out", view.zoom_out, [qt.Qt.CTRL + qt.Qt.Key_Minus]),
        ("Reset Zoom", view.reset_view, [qt.Qt.CTRL + qt.Qt.Key_0]),
    ]
    help_text = []
    for description, slot, keys in shortcuts:
        sequences = [qt.QKeySequence(k) for k in keys]
        for s in sequences:
            qt.QShortcut(s, window, activated=slot)
        help_text.append(
            ", ".join(s.toString() for s in sequences) + f": {description}"
        )
    info.setText("Shortcuts:\n" + "\n".join(help_text))

    # Run the app
    window.showMaximized()
    app.exec_()
