import enable_exr  # noqa: F401
import cv2
import sys
import qt
import numpy
import transform
from layout import HBox


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
        self._transform = transform.fit(dims(self._image), dims(self.sceneRect()))


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

    HBox(window, children=[view])

    window.showMaximized()

    app.exec_()
