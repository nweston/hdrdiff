import enable_exr  # noqa: F401
import cv2
import sys
import qt
import numpy

if __name__ == "__main__":
    img = cv2.imread(sys.argv[1], cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)

    # Convert to 8-bit and add alpha channel to match QImage format
    height, width = img.shape[:2]
    bits = cv2.cvtColor(
        (numpy.clip(img, 0, 1) * 255).astype(numpy.uint8), cv2.COLOR_BGR2BGRA
    ).tobytes()
    qimage = qt.QImage(bits, width, height, width * 4, qt.QImage.Format_RGB32)

    app = qt.QApplication([])
    label = qt.QLabel(f"hello: {sys.argv[1]}")
    label.setPixmap(qt.QPixmap.fromImage(qimage))
    label.show()

    app.exec_()
