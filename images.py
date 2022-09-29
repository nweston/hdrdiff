import enable_exr  # noqa: F401
import cv2
import numpy
import qt


def _qimage_from_rgba(image):
    # Convert to 8-bit to match QImage format
    height, width = image.shape[:2]
    bits = (numpy.clip(image, 0, 1) * 255).astype(numpy.uint8).tobytes()
    return qt.QImage(bits, width, height, width * 4, qt.QImage.Format_RGB32).copy()


def _qimage_from_channel(image, index):
    height, width = image.shape[:2]
    # Transpose to make planar images, and select the channel we want
    channel = image.T[index]
    # Make a 4-channel image and transpose again to pack the pixels
    packed = numpy.array([channel, channel, channel, channel]).T

    bits = (numpy.clip(packed, 0, 1) * 255).astype(numpy.uint8).tobytes()
    return qt.QImage(bits, width, height, width * 4, qt.QImage.Format_RGB32).copy()



class Images(qt.QObject):
    imageChanged = qt.Signal(qt.QImage)

    def __init__(self, filename, **kwargs):
        super().__init__(**kwargs)

        self.cv_image = cv2.cvtColor(
            cv2.imread(filename, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH),
            cv2.COLOR_BGR2BGRA,
        )

        self._channel = None
        self._scale = 1.0
        self._offset = 0.0
        self._update_image()

    def _update_image(self):
        image = self.cv_image * self._scale + self._offset
        if self._channel is None:
            self.qimage = _qimage_from_rgba(image)
        else:
            index = "BGRA".index(self._channel)
            self.qimage = _qimage_from_channel(image, index)
        self.imageChanged.emit(self.qimage)

    def view_channel(self, name):
        if name == self._channel:
            self._channel = None
            self._update_image()
        else:
            self._channel = name
            self._update_image()

    def set_scale(self, value):
        self._scale = value
        self._update_image()

    def set_offset(self, value):
        self._offset = value
        self._update_image()

    def normalize(self):
        low = numpy.min(self.cv_image)
        high = numpy.max(self.cv_image)
        self._scale = 1.0 / (high - low)
        self._offset = -1 * self._scale * low
        self._update_image()
        return self._scale, self._offset
