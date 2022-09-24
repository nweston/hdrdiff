import enable_exr  # noqa: F401
import cv2
import sys
import qt
import numpy
from layout import HBox

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
    scene = qt.QGraphicsScene()
    view = qt.QGraphicsView(scene, parent=window)
    view.setBackgroundBrush(qt.Qt.gray)

    scene.addItem(qt.QGraphicsPixmapItem(qt.QPixmap.fromImage(qimage)))

    HBox(window, children=[view])

    window.showMaximized()

    app.exec_()
