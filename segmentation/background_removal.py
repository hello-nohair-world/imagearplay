import cv2
import numpy as np
import os
import random


class BackgroundRemoval:
    def __init__(self, backgrounds_dir="assets/backgrounds"):
        self.backgrounds_dir = backgrounds_dir
        self.background_files = self._load_background_files()

    def _load_background_files(self):
        """加载背景文件列表"""
        background_files = []
        if os.path.exists(self.backgrounds_dir):
            for filename in os.listdir(self.backgrounds_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    background_files.append(os.path.join(self.backgrounds_dir, filename))
        return background_files

    def green_screen_removal(self, image):
        """绿幕抠图"""
        # 转换到HSV颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 定义绿色范围
        lower_green = np.array([35, 43, 46])
        upper_green = np.array([77, 255, 255])

        # 创建绿色掩码
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # 形态学操作去噪
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 反转掩码（保留前景）
        mask_inv = cv2.bitwise_not(mask)

        # 提取前景
        foreground = cv2.bitwise_and(image, image, mask=mask_inv)

        return foreground, mask_inv

    def skin_segmentation(self, image):
        """肤色分割"""
        # 转换到YCrCb颜色空间
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)

        # 定义肤色范围
        lower_skin = np.array([0, 133, 77])
        upper_skin = np.array([255, 173, 127])

        # 创建肤色掩码
        mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 提取肤色区域
        skin = cv2.bitwise_and(image, image, mask=mask)

        return skin, mask

    def get_random_background(self):
        """获取随机背景图片"""
        if self.background_files:
            background_path = random.choice(self.background_files)
            background = cv2.imread(background_path)
            return background
        return None

    def get_specific_background(self, index=0):
        """获取指定索引的背景图片"""
        if 0 <= index < len(self.background_files) and self.background_files:
            background_path = self.background_files[index]
            background = cv2.imread(background_path)
            return background
        return None

    def get_background_list(self):
        """获取背景文件列表（仅文件名）"""
        if hasattr(self, 'background_files'):
            return [os.path.basename(f) for f in self.background_files]
        return []

    def replace_background(self, image, background_path=None, background_index=None):
        """背景替换"""
        # 进行绿幕抠图
        foreground, mask = self.green_screen_removal(image)

        # 选择背景
        background = None

        # 如果指定了背景索引
        if background_index is not None:
            background = self.get_specific_background(background_index)
        # 如果指定了背景路径
        elif background_path is not None and os.path.exists(background_path):
            background = cv2.imread(background_path)
        # 如果背景文件夹中有图片，随机选择一张
        elif self.background_files:
            background = self.get_random_background()

        # 如果没有可用背景，创建默认蓝色背景
        if background is None:
            background = np.full_like(image, [255, 0, 0], dtype=np.uint8)
        else:
            # 调整背景大小以匹配前景
            background = cv2.resize(background, (image.shape[1], image.shape[0]))

        # 使用掩码合并前景和背景
        mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        result = np.where(mask_3channel == 255, foreground, background)

        return result