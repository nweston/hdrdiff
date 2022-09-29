import enable_exr  # noqa: F401
import cv2
import numpy
import qt
import OpenEXR
import Imath


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


def _read_image(filename):
    img = cv2.imread(filename, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
    if img is None:
        # OpenCV won't read single-channel EXRs, so use OpenEXR
        # directly.
        f = OpenEXR.InputFile(filename)
        assert list(f.header()["channels"].keys()) == ["A"]
        # Get the channel (assume it's alpha for now), and turn into a
        # numpy array
        window = f.header()["dataWindow"]
        width = window.max.x - window.min.x + 1
        height = window.max.y - window.min.y + 1
        alpha = numpy.ndarray(
            (height, width),
            numpy.float32,
            f.channel("A", Imath.PixelType(OpenEXR.FLOAT)),
        )
        # Convert to BGRA
        return cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGRA)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    if img.dtype == numpy.uint8:
        return (img / 255.0).astype(numpy.float32)
    else:
        return img


class Images(qt.QObject):
    imageChanged = qt.Signal(qt.QImage)

    def __init__(self, file1, file2=None, **kwargs):
        super().__init__(**kwargs)

        self.cv_images = [_read_image(f) for f in [file1, file2] if f]

        self._selected_image = 0
        self._channel = None
        self._scale = 1.0
        self._offset = 0.0
        self._update_image()

    @property
    def _cv_image(self):
        return self.cv_images[self._selected_image]

    def _update_image(self):
        image = self._cv_image * self._scale + self._offset
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
        low = min(numpy.min(i) for i in self.cv_images)
        high = min(numpy.max(i) for i in self.cv_images)
        self._scale = 1.0 / (high - low)
        self._offset = -1 * self._scale * low
        self._update_image()
        return self._scale, self._offset

    def select_image(self, index):
        if index not in (0, 1):
            raise ValueError(f"Bad image index: {index}")
        self._selected_image = index
        self._update_image()
