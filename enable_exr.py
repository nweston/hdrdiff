# OpenEXR is disabled by default in opencv (see
# https://github.com/opencv/opencv/issues/21326). Set an environment
# variable to enable it, then re-export everything from cv2.
import os

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
