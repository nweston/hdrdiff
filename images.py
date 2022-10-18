import enable_exr  # noqa: F401
import cv2
import numpy
import qt
import OpenEXR
import Imath
import os.path


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
    img = cv2.imread(
        filename,
        cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_UNCHANGED,
    )
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
        return cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGRA), "A"
    elif img.shape[2] == 3:
        channels = "RGB"
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    else:
        channels = "RGBA"

    if img.dtype == numpy.uint8:
        return (img / 255.0).astype(numpy.float32), channels
    else:
        return img, channels


def _pad_images(images):
    dims = (max(i.shape[0] for i in images), max(i.shape[1] for i in images))
    return [
        i
        if i.shape[:2] == dims
        else cv2.copyMakeBorder(
            i,
            bottom=dims[0] - i.shape[0],
            top=0,
            left=0,
            right=dims[1] - i.shape[1],
            borderType=cv2.BORDER_CONSTANT,
            value=0,
        )
        for i in images
    ]


class Images(qt.QObject):
    imageChanged = qt.Signal(qt.QImage)

    def __init__(self, file1, file2=None, **kwargs):
        super().__init__(**kwargs)

        raw_images, self.descriptions = list(
            zip(*[_read_image(f) for f in [file1, file2] if f])
        )
        self.image_dims = [(i.shape[1], i.shape[0]) for i in raw_images]
        self.cv_images = _pad_images(raw_images)
        self.image_names = [os.path.basename(file1)]
        if len(self.cv_images) == 2:
            self.cv_images.append(numpy.abs(self.cv_images[0] - self.cv_images[1]))
            self.image_names.extend([os.path.basename(file2), "Diff"])
            self.descriptions += (f"max {self.max_diff:g}",)

        self._selected_image = 0
        self._channel = None
        self._scale = [1.0] * len(self.cv_images)
        self._offset = [0.0] * len(self.cv_images)
        self._update_image()

    def _update_image(self):
        i = self._selected_image
        image = self.cv_images[i] * self._scale[i] + self._offset[i]
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
        self._scale[0] = self._scale[1] = value
        self._update_image()

    def set_offset(self, value):
        self._offset[0] = self._offset[1] = value
        self._update_image()

    def normalize(self):
        low = min(numpy.min(i) for i in self.cv_images)
        high = max(numpy.max(i) for i in self.cv_images)
        self._scale[0] = self._scale[1] = 1.0 / (high - low)
        self._offset[0] = self._offset[1] = -1 * self._scale[0] * low
        self._update_image()
        return self._scale[0], self._offset[0]

    def set_diff_scale(self, value):
        self._scale[2] = value
        self._update_image()

    def normalize_diff(self):
        if len(self.cv_images) < 3:
            return 1.0

        self._scale[2] = 1.0 / self.max_diff
        self._update_image()
        return self._scale[2]

    def select_image(self, index):
        if index >= len(self.cv_images):
            return
        self._selected_image = index
        self._update_image()

    @property
    def selected_image(self):
        return self._selected_image

    @property
    def max_diff(self):
        return numpy.max(self.cv_images[2])

    @property
    def has_diff(self):
        return len(self.cv_images) == 3
