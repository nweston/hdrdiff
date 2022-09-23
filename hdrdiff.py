import enable_exr  # noqa: F401
import cv2
import sys

if __name__ == "__main__":
    img = cv2.imread(sys.argv[1], cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
    print(img)
