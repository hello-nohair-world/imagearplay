import cv2
import numpy as np
from pyzbar import pyzbar


class QRSticker:
    @staticmethod
    def detect_qr_codes(image):
        """检测二维码"""
        # 解码二维码
        decoded_objects = pyzbar.decode(image)

        # 在图像上绘制二维码边界框
        result_image = image.copy()
        for obj in decoded_objects:
            # 获取二维码的边界框
            points = obj.polygon
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                hull = list(map(tuple, np.squeeze(hull)))
            else:
                hull = points

            # 绘制边界框
            n = len(hull)
            for j in range(0, n):
                cv2.line(result_image, hull[j], hull[(j + 1) % n], (255, 0, 0), 3)

            # 显示二维码数据
            x = obj.rect.left
            y = obj.rect.top
            cv2.putText(result_image, obj.data.decode("utf-8"), (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        return result_image, decoded_objects

    @staticmethod
    def add_sticker_on_qr(image, sticker_path="assets/stickers/star.png"):
        """在检测到的二维码上添加贴纸"""
        # 检测二维码
        result_image, decoded_objects = QRSticker.detect_qr_codes(image)

        # 加载贴纸
        if sticker_path and cv2.imread(sticker_path) is not None:
            sticker = cv2.imread(sticker_path, cv2.IMREAD_UNCHANGED)
        else:
            # 创建默认贴纸（五角星）
            sticker = np.zeros((50, 50, 4), dtype=np.uint8)
            # 绘制一个简单的五角星
            pts = np.array([[25, 5], [35, 20], [50, 20], [38, 30], [43, 45],
                            [25, 35], [7, 45], [12, 30], [0, 20], [15, 20]], np.int32)
            cv2.fillPoly(sticker, [pts], (0, 255, 255, 255))

        # 在每个二维码中心添加贴纸
        for obj in decoded_objects:
            # 计算二维码中心点
            center_x = obj.rect.left + obj.rect.width // 2
            center_y = obj.rect.top + obj.rect.height // 2

            # 调整贴纸大小
            sticker_resized = cv2.resize(sticker, (obj.rect.width // 2, obj.rect.height // 2))

            # 计算贴纸位置
            sticker_x = center_x - sticker_resized.shape[1] // 2
            sticker_y = center_y - sticker_resized.shape[0] // 2

            # 确保贴纸在图像范围内
            if (sticker_x >= 0 and sticker_y >= 0 and
                    sticker_x + sticker_resized.shape[1] <= image.shape[1] and
                    sticker_y + sticker_resized.shape[0] <= image.shape[0]):

                # 分离贴纸的alpha通道
                if sticker_resized.shape[2] == 4:
                    sticker_rgb = sticker_resized[:, :, :3]
                    sticker_alpha = sticker_resized[:, :, 3] / 255.0
                else:
                    sticker_rgb = sticker_resized
                    sticker_alpha = np.ones((sticker_resized.shape[0], sticker_resized.shape[1]))

                # 在图像上叠加贴纸
                for c in range(0, 3):
                    result_image[sticker_y:sticker_y + sticker_resized.shape[0],
                    sticker_x:sticker_x + sticker_resized.shape[1], c] = \
                        (sticker_alpha * sticker_rgb[:, :, c] +
                         (1 - sticker_alpha) * result_image[sticker_y:sticker_y + sticker_resized.shape[0],
                                               sticker_x:sticker_x + sticker_resized.shape[1], c])

        return result_image
    