import enable_exr  # noqa: F401
import cv2
import numpy
import qt


def _qimage_from_rgba(image):
    # Convert to 8-bit to match QImage format
    height, width = image.shape[:2]
    bits = (numpy.clip(image, 0, 1) * 255).astype(numpy.uint8).tobytes()
    return qt.QImage(bits, width, height, width * 4, qt.QImage.Format_RGB32)


def _qimage_from_channel(image, index):
    height, width = image.shape[:2]
    # Transpose to make planar images, and select the channel we want
    channel = image.T[index]
    # Make a 4-channel image and transpose again to pack the pixels
    packed = numpy.array([channel, channel, channel, channel]).T

    bits = (numpy.clip(packed, 0, 1) * 255).astype(numpy.uint8).tobytes()
    return qt.QImage(bits, width, height, width * 4, qt.QImage.Format_RGB32)


class Images(qt.QObject):
    imageChanged = qt.Signal(qt.QImage)

    def __init__(self, filename, **kwargs):
        super().__init__(**kwargs)

        self.cv_image = cv2.cvtColor(
            cv2.imread(filename, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH),
            cv2.COLOR_BGR2BGRA,
        )

        self.qimage = _qimage_from_rgba(self.cv_image)
        self._channel = None

    def _set_image(self, image):
        self.qimage = image
        self.imageChanged.emit(image)

    def view_channel(self, name):
        if name == self._channel:
            self._channel = None
            self._set_image(_qimage_from_rgba(self.cv_image))
        else:
            self._channel = name
            index = "BGRA".index(name)
            self._set_image(_qimage_from_channel(self.cv_image, index))
