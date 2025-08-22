import cv2
import mediapipe as mp
import numpy as np
import os
import math

class PoseEstimation:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=5,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def estimate_pose(self, image):
        """姿态估计"""
        # 转换颜色空间
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 处理图像
        results = self.face_mesh.process(rgb_image)

        # 在图像上绘制面部网格
        annotated_image = image.copy()
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                self.mp_drawing.draw_landmarks(
                    image=annotated_image,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles
                    .get_default_face_mesh_tesselation_style())

                self.mp_drawing.draw_landmarks(
                    image=annotated_image,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles
                    .get_default_face_mesh_contours_style())

                self.mp_drawing.draw_landmarks(
                    image=annotated_image,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_IRISES,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles
                    .get_default_face_mesh_iris_connections_style())

        return annotated_image

    def add_nose_ring(self, image):
        """在鼻子上添加装饰"""
        # 转换颜色空间
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 处理图像
        results = self.face_mesh.process(rgb_image)

        # 复制原始图像
        annotated_image = image.copy()

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # 获取鼻子关键点（索引为1）
                nose_landmark = face_landmarks.landmark[1]

                # 将归一化坐标转换为像素坐标
                image_height, image_width, _ = annotated_image.shape
                nose_x = int(nose_landmark.x * image_width)
                nose_y = int(nose_landmark.y * image_height)

                # 绘制一个简单的圆环作为鼻环
                cv2.circle(annotated_image, (nose_x, nose_y), 10, (0, 255, 255), 2)
                cv2.circle(annotated_image, (nose_x, nose_y), 5, (0, 255, 255), -1)

        return annotated_image

    def add_sunglasses(self, image, glasses_path="assets/stickers/sunglasses.png"):
        """添加墨镜特效（基于姿态估计，支持头部倾斜）"""
        # 转换颜色空间以供MediaPipe处理
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 处理图像，获取面部网格
        results = self.face_mesh.process(rgb_image)

        # 复制原始图像作为结果图像
        result_image = image.copy()

        # 检查是否检测到人脸
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # --- 关键点选择 ---
                # 左眼外角 (通常是点 33) 和内角 (通常是点 133)
                left_eye_outer = face_landmarks.landmark[33]
                left_eye_inner = face_landmarks.landmark[133]

                # 右眼外角 (通常是点 263) 和内角 (通常是点 362)
                right_eye_outer = face_landmarks.landmark[263]
                right_eye_inner = face_landmarks.landmark[362]

                # --- 计算眼睛中心点 (像素坐标) ---
                image_height, image_width = image.shape[:2]

                left_eye_center_x_px = int((left_eye_outer.x + left_eye_inner.x) / 2.0 * image_width)
                left_eye_center_y_px = int((left_eye_outer.y + left_eye_inner.y) / 2.0 * image_height)

                right_eye_center_x_px = int((right_eye_outer.x + right_eye_inner.x) / 2.0 * image_width)
                right_eye_center_y_px = int((right_eye_outer.y + right_eye_inner.y) / 2.0 * image_height)

                # --- 计算眼睛连线的角度 (弧度) ---
                # 计算从左眼中心到右眼中心的向量
                delta_x = right_eye_center_x_px - left_eye_center_x_px
                delta_y = right_eye_center_y_px - left_eye_center_y_px

                # 使用 atan2 计算角度（考虑象限），得到的是从左眼指向右眼的向量与水平轴的夹角
                angle_rad = math.atan2(delta_y, delta_x)
                # 转换为角度
                angle_deg = math.degrees(angle_rad)

                # --- 估算眼镜尺寸 ---
                # 计算两眼中心的距离
                eye_distance_px = math.sqrt(delta_x ** 2 + delta_y ** 2)

                # 估算眼镜的宽度 (略大于两眼距离)
                glasses_width_ratio = 2.1  # 可以微调
                glasses_width_px = int(eye_distance_px * glasses_width_ratio)

                # 估算眼镜的高度 (基于宽度的一个比例)
                glasses_height_ratio = 0.45  # 可以微调
                glasses_height_px = int(glasses_width_px * glasses_height_ratio)

                # --- 计算眼镜中心点 (像素坐标) ---
                glasses_center_x_px = (left_eye_center_x_px + right_eye_center_x_px) // 2
                glasses_center_y_px = (left_eye_center_y_px + right_eye_center_y_px) // 2

                # --- 加载和处理墨镜图像 ---
                # 1. 加载墨镜图像
                if os.path.exists(glasses_path):
                    glasses_img = cv2.imread(glasses_path, cv2.IMREAD_UNCHANGED)
                else:
                    # 如果墨镜图像不存在，创建一个简单的默认墨镜
                    glasses_img = np.zeros((glasses_height_px if glasses_height_px > 0 else 50,
                                            glasses_width_px if glasses_width_px > 0 else 100, 4), dtype=np.uint8)
                    glasses_img[:, :, 0] = 0  # B
                    glasses_img[:, :, 1] = 0  # G
                    glasses_img[:, :, 2] = 0  # R
                    glasses_img[:, :, 3] = 128  # Alpha (半透明)

                    # 添加镜片 (白色半透明)
                    if glasses_width_px > 20 and glasses_height_px > 10:
                        left_lens_center_x = int(glasses_width_px * 0.25)
                        left_lens_center_y = int(glasses_height_px * 0.5)
                        right_lens_center_x = int(glasses_width_px * 0.75)
                        right_lens_center_y = int(glasses_height_px * 0.5)
                        lens_radius_x = int(glasses_width_px * 0.15)
                        lens_radius_y = int(glasses_height_px * 0.4)
                        cv2.ellipse(glasses_img,
                                    (left_lens_center_x, left_lens_center_y),
                                    (lens_radius_x, lens_radius_y),
                                    0, 0, 360,
                                    (255, 255, 255, 100), -1)
                        cv2.ellipse(glasses_img,
                                    (right_lens_center_x, right_lens_center_y),
                                    (lens_radius_x, lens_radius_y),
                                    0, 0, 360,
                                    (255, 255, 255, 100), -1)

                # 2. 调整墨镜图像大小
                if glasses_width_px > 0 and glasses_height_px > 0:
                    try:
                        glasses_resized = cv2.resize(glasses_img, (glasses_width_px, glasses_height_px))
                    except cv2.error:
                        # 如果调整大小失败，则跳过此人脸
                        continue
                else:
                    continue  # 尺寸无效则跳过

                # --- 旋转墨镜图像 ---
                # 1. 获取旋转矩阵 (围绕墨镜图像的中心旋转)
                center_of_glasses = (glasses_width_px // 2, glasses_height_px // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center_of_glasses, -angle_deg, 1.0)  # 注意角度符号

                # 2. 计算旋转后的边界框尺寸，避免裁剪
                abs_cos = abs(rotation_matrix[0, 0])
                abs_sin = abs(rotation_matrix[0, 1])
                new_glasses_width = int(glasses_height_px * abs_sin + glasses_width_px * abs_cos)
                new_glasses_height = int(glasses_height_px * abs_cos + glasses_width_px * abs_sin)

                # 3. 调整旋转矩阵的平移部分，使图像居中
                rotation_matrix[0, 2] += new_glasses_width / 2 - center_of_glasses[0]
                rotation_matrix[1, 2] += new_glasses_height / 2 - center_of_glasses[1]

                # 4. 执行旋转 (处理 Alpha 通道)
                rotated_glasses_bgr = cv2.warpAffine(glasses_resized[:, :, :3], rotation_matrix,
                                                     (new_glasses_width, new_glasses_height),
                                                     flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                                     borderValue=(0, 0, 0))
                rotated_glasses_alpha = cv2.warpAffine(glasses_resized[:, :, 3], rotation_matrix,
                                                       (new_glasses_width, new_glasses_height),
                                                       flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                                       borderValue=0)

                # --- 计算在原图上的放置位置 ---
                # 旋转后的新中心点作为放置点
                final_x_px = glasses_center_x_px - new_glasses_width // 2
                final_y_px = glasses_center_y_px - new_glasses_height // 2

                # --- 边界检查和叠加 ---
                # 确保放置区域在原图范围内
                if final_x_px >= image_width or final_y_px >= image_height or \
                        (final_x_px + new_glasses_width) <= 0 or (final_y_px + new_glasses_height) <= 0:
                    continue  # 完全在图像外，跳过

                # 计算实际需要叠加的区域
                x_start_src = max(0, -final_x_px)
                x_end_src = new_glasses_width + min(0, image_width - (final_x_px + new_glasses_width))
                y_start_src = max(0, -final_y_px)
                y_end_src = new_glasses_height + min(0, image_height - (final_y_px + new_glasses_height))

                x_start_dst = max(0, final_x_px)
                x_end_dst = min(image_width, final_x_px + new_glasses_width)
                y_start_dst = max(0, final_y_px)
                y_end_dst = min(image_height, final_y_px + new_glasses_height)

                # 获取源区域 (旋转后的墨镜)
                overlay_region_bgr = rotated_glasses_bgr[y_start_src:y_end_src, x_start_src:x_end_src]
                overlay_region_alpha = rotated_glasses_alpha[y_start_src:y_end_src, x_start_src:x_end_src] / 255.0

                # 获取目标区域 (原图)
                background_region = result_image[y_start_dst:y_end_dst, x_start_dst:x_end_dst]

                # 执行 Alpha 混合
                for c in range(0, 3):
                    background_region[:, :, c] = (
                            overlay_region_alpha * overlay_region_bgr[:, :, c] +
                            (1 - overlay_region_alpha) * background_region[:, :, c]
                    )

                # 将混合后的区域放回结果图像
                result_image[y_start_dst:y_end_dst, x_start_dst:x_end_dst] = background_region

        return result_image
