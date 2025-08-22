import cv2
import numpy as np


class BasicFilters:
    @staticmethod
    def grayscale(image):
        """灰度滤镜"""
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def binary(image, threshold=127):
        """二值化滤镜"""
        gray = BasicFilters.grayscale(image)
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        return binary

    @staticmethod
    def invert(image):
        """反色滤镜"""
        return 255 - image

    @staticmethod
    def histogram_equalization(image):
        """直方图均衡化"""
        # 转换到YUV颜色空间
        yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
        # 对Y通道进行直方图均衡化
        yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
        # 转换回BGR颜色空间
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

    @staticmethod
    def brightness_contrast(image, brightness=0, contrast=1.0):
        """亮度对比度调整"""
        return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)
