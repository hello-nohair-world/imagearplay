import cv2
import numpy as np


class ArtisticFilters:
    @staticmethod
    def edge_detection(image):
        """线描滤镜"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        return 255-cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    @staticmethod
    def sketch_filter(image):
        """素描滤镜"""
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 反色处理
        inverted = 255 - gray

        # 高斯模糊
        blurred = cv2.GaussianBlur(inverted, (21, 21), 0)

        # 颜色减淡
        sketch = cv2.divide(gray, 255 - blurred, scale=256)

        return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)

    @staticmethod
    def cartoon_filter(image):
        """卡通滤镜"""
        # 边缘保留滤波
        cartoon = cv2.stylization(image, sigma_s=60, sigma_r=0.6)

        # 边缘增强
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.medianBlur(gray, 7)
        edges = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # 合并结果
        result = cv2.bitwise_and(cartoon, edges)
        return result

    @staticmethod
    def oil_painting(image):
        """油画滤镜"""
        # 使用OpenCV的油画效果函数
        return cv2.xphoto.oilPainting(image, 7, 1)
