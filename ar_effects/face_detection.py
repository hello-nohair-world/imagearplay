import cv2
import numpy as np
import os


class FaceDetection:
    def __init__(self):
        # 加载Haar级联分类器
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def detect_faces(self, image):
        """检测人脸并绘制矩形框"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 检测人脸
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        # 在图像上绘制人脸矩形框
        result_image = image.copy()
        for (x, y, w, h) in faces:
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (255, 0, 0), 2)

        return result_image, faces

    def detect_faces_no_drawing(self, image):
        """检测人脸但不绘制矩形框（用于虚拟帽子）"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 检测人脸
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        # 不绘制任何框，直接返回原图和检测到的人脸坐标
        return image.copy(), faces

    def add_virtual_hat(self, image, hat_path="assets/stickers/hat.png"):
        """添加虚拟帽子（不绘制人脸框）"""
        # 检测人脸但不绘制框
        result_image, faces = self.detect_faces_no_drawing(image)

        # 加载帽子图像
        if os.path.exists(hat_path):
            hat = cv2.imread(hat_path, cv2.IMREAD_UNCHANGED)
        else:
            # 如果帽子图像不存在，创建一个简单的帽子
            hat = np.zeros((100, 100, 4), dtype=np.uint8)
            # 创建一个红色的帽子形状
            # 帽子顶部（矩形）
            hat[20:40, 10:90, 0] = 0  # B
            hat[20:40, 10:90, 1] = 0  # G
            hat[20:40, 10:90, 2] = 255  # R
            hat[20:40, 10:90, 3] = 255  # Alpha

            # 帽子底部（弧形）
            for i in range(10, 90):
                y_pos = int(40 + 20 * (1 - abs(i - 50) / 40))
                if y_pos < 70:
                    hat[y_pos:y_pos + 5, i:i + 2, 0] = 0
                    hat[y_pos:y_pos + 5, i:i + 2, 1] = 0
                    hat[y_pos:y_pos + 5, i:i + 2, 2] = 255
                    hat[y_pos:y_pos + 5, i:i + 2, 3] = 255

        # 为每个人脸添加帽子
        for (x, y, w, h) in faces:
            # 调整帽子大小以适应人脸宽度
            hat_width = w
            hat_height = int(h * 0.4)  # 帽子高度为人脸高度的40%
            hat_resized = cv2.resize(hat, (hat_width, hat_height))

            # 计算帽子位置（在人脸顶部）
            y_offset = max(0, y - int(hat_height * 0.7))  # 帽子稍微覆盖额头
            x_offset = x

            # 确保帽子在图像范围内
            if y_offset >= 0 and y_offset + hat_resized.shape[0] <= result_image.shape[0]:
                # 分离帽子的alpha通道
                if hat_resized.shape[2] == 4:
                    hat_rgb = hat_resized[:, :, :3]
                    hat_alpha = hat_resized[:, :, 3] / 255.0
                else:
                    hat_rgb = hat_resized
                    hat_alpha = np.ones((hat_resized.shape[0], hat_resized.shape[1]))

                # 在图像上叠加帽子
                for c in range(0, 3):
                    result_image[y_offset:y_offset + hat_resized.shape[0],
                    x_offset:x_offset + hat_resized.shape[1], c] = \
                        (hat_alpha * hat_rgb[:, :, c] +
                         (1 - hat_alpha) * result_image[y_offset:y_offset + hat_resized.shape[0],
                                           x_offset:x_offset + hat_resized.shape[1], c])

        return result_image
