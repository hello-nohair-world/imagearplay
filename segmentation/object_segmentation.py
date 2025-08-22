import cv2
import numpy as np


class ObjectSegmentation:
    @staticmethod
    def canny_edge_segmentation(image):
        """Canny边缘分割"""
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 应用高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny边缘检测
        edges = cv2.Canny(blurred, 50, 150)

        # 形态学操作连接边缘
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    @staticmethod
    def watershed_segmentation(image):
        """分水岭算法分割"""
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 去噪（高斯模糊）
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # 应用阈值分割（使用OTSU自动阈值）
        ret, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 噪声去除（形态学开运算）
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

        # 确定背景区域（膨胀操作）
        sure_bg = cv2.dilate(opening, kernel, iterations=3)

        # 确定前景区域（距离变换+阈值处理）
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        ret, sure_fg = cv2.threshold(dist_transform, 0.5 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)

        # 找到未知区域（背景减去前景）
        unknown = cv2.subtract(sure_bg, sure_fg)

        # 标记连通区域
        ret, markers = cv2.connectedComponents(sure_fg)

        # 调整标记（背景设为1，其他递增）
        markers = markers + 1

        # 标记未知区域为0
        markers[unknown == 255] = 0

        # 应用分水岭算法
        markers = cv2.watershed(image, markers)

        # 标记边界为红色
        image[markers == -1] = [0, 0, 255]

        return image

    @staticmethod
    def connected_components(image):
        """连通域分析"""
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 应用阈值
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        # 查找连通域
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

        # 创建彩色标记图像
        colored_labels = np.zeros((labels.shape[0], labels.shape[1], 3), dtype=np.uint8)

        # 为每个连通域分配随机颜色
        colors = np.random.randint(0, 255, size=(num_labels, 3), dtype=np.uint8)
        colors[0] = [0, 0, 0]  # 背景设为黑色

        for i in range(num_labels):
            colored_labels[labels == i] = colors[i]

        return colored_labels
