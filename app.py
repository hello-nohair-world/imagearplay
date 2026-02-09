# app.py
import os
import uuid
import base64
from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
from PIL import Image
import io

# --- 导入您的模块 ---
try:
    from filters.basic_filters import BasicFilters
    from filters.artistic_filters import ArtisticFilters
    from filters.enhancement import ImageEnhancement
    from segmentation.background_removal import BackgroundRemoval
    from segmentation.object_segmentation import ObjectSegmentation
    from ar_effects.face_detection import FaceDetection
    from ar_effects.qr_sticker import QRSticker
    from ar_effects.pose_estimation import PoseEstimation
except ImportError as e:
    print(f"[ERROR] 请将 filters/, segmentation/, ar_effects/ 放入项目根目录！")
    exit(1)

app = Flask(__name__)
app.secret_key = 'flask_ar_2026'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 实例化
basic_filters = BasicFilters()
artistic_filters = ArtisticFilters()
enhancement = ImageEnhancement()
bg_removal = BackgroundRemoval()
obj_segmentation = ObjectSegmentation()
face_detection = FaceDetection()
qr_sticker = QRSticker()
pose_estimation = PoseEstimation()


# --- 辅助函数 ---
def opencv_to_base64(image):
    if image is None or image.size == 0:
        raise ValueError("Invalid image")
    # 转 BGR
    if len(image.shape) == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    elif len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    # 编码
    success, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not success or len(buffer) == 0:
        raise ValueError("cv2.imencode failed")
    img_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{img_str}"

def base64_to_opencv(img_data):
    try:
        if not img_data.startswith('data:image/'):
            raise ValueError("Not a data URL")
        header, encoded = img_data.split(',', 1)
        decoded = base64.b64decode(encoded)
        np_arr = np.frombuffer(decoded, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            # fallback to PIL
            pil_img = Image.open(io.BytesIO(decoded))
            if pil_img.mode != 'RGB':
                pil_img = pil_img.convert('RGB')
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return img
    except Exception as e:
        raise ValueError(f"Decode failed: {e}")


# === 历史管理器（严格复刻 main.py）===
class HistoryManager:
    def __init__(self):
        self.history = []          # list of np.ndarray (BGR)
        self.history_index = -1    # 当前指向的位置
        self.original_image = None # 原始图
        self.max_history = 20

    def add(self, image):
        """添加图像到历史（复制）"""
        if image is None:
            return
        # 如果不在末尾，截断后续
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        # 添加新图像
        self.history.append(image.copy())
        self.history_index += 1
        # 限制长度
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self):
        if self.history_index <= 0:
            return None
        self.history_index -= 1
        return self.history[self.history_index].copy()

    def redo(self):
        if self.history_index >= len(self.history) - 1:
            return None
        self.history_index += 1
        return self.history[self.history_index].copy()

    def save_current(self):
        """保存当前状态：覆盖 history[history_index]，并锁定（禁用 undo/redo）"""
        if self.history_index >= 0 and self.history_index < len(self.history):
            self.history[self.history_index] = self.history[self.history_index].copy()
            # 🔒 关键：锁定状态 → 将索引设为 -1（表示无有效历史位置）
            self.history_index = -1

    def reset_to_original(self, original):
        """重置：清空历史，仅保留 original，并添加“重置”操作"""
        if original is not None:
            self.original_image = original.copy()
            self.history = [original.copy()]
            self.history_index = 0  # 指向重置后的状态

    def can_undo(self):
        return self.history_index > 0

    def can_redo(self):
        return self.history_index >= 0 and self.history_index < len(self.history) - 1


history_manager = HistoryManager()


# --- 路由 ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json()
    if not data or 'file' not in data:
        return jsonify({'success': False, 'error': '缺少 file 字段'}), 400
    img_data = data['file']
    try:
        image = base64_to_opencv(img_data)
        # 初始化历史
        history_manager.reset_to_original(image)
        image_base64 = opencv_to_base64(image)
        return jsonify({'success': True, 'image': image_base64})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/process', methods=['POST'])
def process_image():
    data = request.get_json()
    action = data.get('action')
    img_data = data.get('image')
    if not img_data or not action:
        return jsonify({'success': False, 'error': 'Missing image or action'}), 400

    try:
        image = base64_to_opencv(img_data)
        result = None

        # --- 处理各种操作（严格按 main.py）---
        if action == 'grayscale':
            res_gray = basic_filters.grayscale(image)
            result = cv2.cvtColor(res_gray, cv2.COLOR_GRAY2BGR)
        elif action == 'binary':
            res_gray = basic_filters.binary(image)
            result = cv2.cvtColor(res_gray, cv2.COLOR_GRAY2BGR)
        elif action == 'invert':
            result = basic_filters.invert(image)
        elif action == 'histogram_equalization':
            result = basic_filters.histogram_equalization(image)
        elif action == 'edge_detection':
            result = artistic_filters.edge_detection(image)
        elif action == 'sketch':
            result = artistic_filters.sketch_filter(image)
        elif action == 'cartoon':
            result = artistic_filters.cartoon_filter(image)
        elif action == 'oil_painting':
            result = artistic_filters.oil_painting(image)
        elif action == 'gaussian_blur':
            result = enhancement.gaussian_blur(image)
        elif action == 'median_blur':
            result = enhancement.median_blur(image)
        elif action == 'bilateral_filter':
            result = enhancement.bilateral_filter(image)
        elif action == 'sharpen':
            result = enhancement.sharpen(image)
        elif action == 'unsharp_mask':
            result = enhancement.unsharp_mask(image)
        elif action == 'green_screen_removal':
            result, _ = bg_removal.green_screen_removal(image)
        elif action == 'skin_segmentation':
            result, _ = bg_removal.skin_segmentation(image)
        elif action == 'replace_background':
            result = bg_removal.replace_background(image)
        elif action == 'canny_segmentation':
            result = obj_segmentation.canny_edge_segmentation(image)
        elif action == 'watershed_segmentation':
            result = obj_segmentation.watershed_segmentation(image)
        elif action == 'connected_components':
            result = obj_segmentation.connected_components(image)
        elif action == 'detect_faces':
            result, _ = face_detection.detect_faces(image)
        elif action == 'add_virtual_hat':
            result = face_detection.add_virtual_hat(image)
        elif action == 'apply_qr_sticker':
            result = qr_sticker.add_sticker_on_qr(image)
        elif action == 'estimate_pose':
            result = pose_estimation.estimate_pose(image)
        elif action == 'add_nose_ring':
            result = pose_estimation.add_nose_ring(image)
        elif action == 'add_sunglasses':
            result = pose_estimation.add_sunglasses(image)
        elif action == 'adjust_final':
            brightness = data.get('brightness', 0)
            contrast = data.get('contrast', 1.0)
            result = basic_filters.brightness_contrast(image, brightness=brightness, contrast=contrast)
        else:
            return jsonify({'success': False, 'error': f'未知操作: {action}'}), 400

        if result is not None:
            # ✅ 严格复刻 main.py：add_to_history
            history_manager.add(result)
            return jsonify({'success': True, 'image': opencv_to_base64(result)})
        else:
            return jsonify({'success': False, 'error': '处理未返回图像'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# === 新增：只读状态查询接口 ===
@app.route('/history/status', methods=['GET'])
def get_history_status():
    """返回当前历史状态（只读）"""
    return jsonify({
        'success': True,
        'can_undo': history_manager.can_undo(),
        'can_redo': history_manager.can_redo(),
        'history_index': history_manager.history_index,
        'history_length': len(history_manager.history)
    })

# === 保留原操作接口，但改为 POST 且不用于状态检查 ===
@app.route('/history/undo', methods=['POST'])
def undo():
    img = history_manager.undo()
    if img is None:
        return jsonify({'success': False, 'error': '无更多可撤回操作'}), 400
    return jsonify({'success': True, 'image': opencv_to_base64(img)})

@app.route('/history/redo', methods=['POST'])
def redo():
    img = history_manager.redo()
    if img is None:
        return jsonify({'success': False, 'error': '无更多可恢复操作'}), 400
    return jsonify({'success': True, 'image': opencv_to_base64(img)})

@app.route('/history/save', methods=['POST'])
def save_progress():
    # ✅ 严格复刻 main.py：save_current → 锁定状态
    history_manager.save_current()
    return jsonify({'success': True, 'locked': True})

@app.route('/history/reset', methods=['POST'])
def reset_image():
    if history_manager.original_image is not None:
        original = history_manager.original_image.copy()
        history_manager.reset_to_original(original)
        return jsonify({'success': True, 'image': opencv_to_base64(original)})
    return jsonify({'success': False, 'error': '无原始图像'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)