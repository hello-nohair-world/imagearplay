# app.py
import os
import uuid
import base64
from flask import Flask, render_template, request, jsonify, send_file, url_for
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


# === 历史管理器（严格复刻逻辑并修复边界情况）===
class HistoryManager:
    def __init__(self):
        self.history = []  # list of np.ndarray (BGR)
        self.history_index = -1  # 当前指向的位置 (-1 表示无效/锁定/空)
        self.original_image = None  # 原始图
        self.max_history = 20

    def add(self, image):
        """
        规则1：添加历史记录
        若在历史中间状态执行新操作，需截断该状态之后的所有记录。
        对图像进行深拷贝并追加到历史列表末尾，同时更新索引指向新记录。
        """
        if image is None:
            return

        # ✅ 修复：如果当前处于 "锁定" 状态 (index == -1) 或者在中间状态
        # 规则要求：如果在中间状态，截断后续。
        # 如果 index 是 -1 (刚保存过)，我们应该把当前图像作为新的 "基准" 开始记录吗？
        # 根据 Tkinter 逻辑和通常的 "保存进度" 含义：
        # 保存进度后，用户做新操作，这个新操作应该是基于保存点的。
        # 此时 history 列表里还有旧数据，但 index 是 -1。
        # 策略：如果 index == -1，我们不清空历史，而是将 index 重置为 len-1 (指向最后一个保存的状态)
        # 然后执行正常的 "截断+添加" 逻辑。这样新操作就接在保存点后面了。

        if self.history_index == -1:
            if len(self.history) > 0:
                # 恢复到最后一个有效状态，作为新操作的起点
                self.history_index = len(self.history) - 1
            else:
                # 极端情况：历史为空，直接添加
                self.history.append(image.copy())
                self.history_index = 0
                return

        # 如果在中间状态 (index < len - 1)，截断后续
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
        """规则2：撤回操作"""
        # 条件检查：仅当 self.history_index > 0 时可执行
        if self.history_index <= 0:
            return None
        self.history_index -= 1
        return self.history[self.history_index].copy()

    def redo(self):
        """规则3：恢复操作"""
        # 条件检查：仅当 self.history_index < len(self.history) - 1 时可执行
        # 注意：如果 history_index 是 -1，这个条件肯定不满足 (因为 len >= 0, -1 < len-1 可能成立，但逻辑上 -1 是无状态)
        # 所以必须先检查 index 是否有效 (>=0)
        if self.history_index < 0 or self.history_index >= len(self.history) - 1:
            return None
        self.history_index += 1
        return self.history[self.history_index].copy()

    def save_current(self):
        """
        规则4：保存进度
        更新历史：将当前图像副本更新到历史列表中 self.history_index 指向的位置。
        禁用按钮：将索引设为 -1，模拟 "锁定"。
        """
        if self.history_index >= 0 and self.history_index < len(self.history):
            # 覆盖当前状态（虽然通常不需要深拷贝覆盖自己，但为了保险）
            self.history[self.history_index] = self.history[self.history_index].copy()

        # 🔒 关键：锁定状态 → 将索引设为 -1
        # 这会导致 can_undo (index > 0) 为 False
        # 这会导致 can_redo (index < len - 1 AND index >= 0) 为 False
        self.history_index = -1

    def reset_to_original(self, original):
        """重置：清空历史，仅保留 original"""
        if original is not None:
            self.original_image = original.copy()
            self.history = [original.copy()]
            self.history_index = 0

    def can_undo(self):
        # 规则5：self.history_index > 0
        return self.history_index > 0

    def can_redo(self):
        # 规则5：self.history_index < len(self.history) - 1
        # 隐含条件：history_index 必须 >= 0 才有意义
        if self.history_index < 0:
            return False
        return self.history_index < len(self.history) - 1


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


# 在 app.py 中添加以下路由

# === 保存图像路由 ===
@app.route('/save', methods=['POST'])
def save_image():
    """保存当前图像"""
    data = request.get_json()
    img_data = data.get('image')

    if not img_data:
        return jsonify({'success': False, 'error': '缺少图像数据'}), 400

    try:
        image = base64_to_opencv(img_data)

        # 生成文件名
        filename = f"processed_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # 保存图像
        cv2.imwrite(filepath, image)

        # 返回下载 URL
        download_url = url_for('download_file', filename=filename, _external=True)

        return jsonify({
            'success': True,
            'download_url': download_url,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# === 下载文件路由 ===
@app.route('/download/<filename>')
def download_file(filename):
    """下载处理后的图像"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'success': False, 'error': '文件不存在'}), 404


# === 背景列表路由 ===
@app.route('/backgrounds/list', methods=['GET'])
def get_background_list():
    """获取可用背景列表"""
    try:
        backgrounds = bg_removal.get_background_list()
        return jsonify({
            'success': True,
            'backgrounds': backgrounds
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# === 更新 process_image 路由，添加背景替换变体 ===
# 在原有的 process_image 函数中添加以下处理分支：



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

        # --- 处理各种操作 ---
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
        elif action == 'replace_background_random':
            result = bg_removal.replace_background(image, background_index=None)
        elif action == 'replace_background_default':
            result = bg_removal.replace_background(image, background_index=-1)
        elif action == 'replace_background_selected':
            bg_index = data.get('background_index', 0)
            result = bg_removal.replace_background(image, background_index=bg_index)
        elif action == 'adjust_final':
            brightness = data.get('brightness', 0)
            contrast = data.get('contrast', 1.0)
            result = basic_filters.brightness_contrast(image, brightness=brightness, contrast=contrast)
        else:
            return jsonify({'success': False, 'error': f'未知操作：{action}'}), 400

        if result is not None:
            # 添加历史记录
            history_manager.add(result)

            return jsonify({
                'success': True,
                'image': opencv_to_base64(result),
                'can_undo': history_manager.can_undo(),
                'can_redo': history_manager.can_redo()
            })
        else:
            return jsonify({'success': False, 'error': '处理未返回图像'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# === 历史 API ===
@app.route('/history/undo', methods=['POST'])
def undo():
    img = history_manager.undo()
    if img is None:
        return jsonify({
            'success': False,
            'error': '无更多可撤回操作',
            'can_undo': history_manager.can_undo(),
            'can_redo': history_manager.can_redo()
        }), 400

    return jsonify({
        'success': True,
        'image': opencv_to_base64(img),
        'can_undo': history_manager.can_undo(),
        'can_redo': history_manager.can_redo()
    })


@app.route('/history/redo', methods=['POST'])
def redo():
    img = history_manager.redo()
    if img is None:
        return jsonify({
            'success': False,
            'error': '无更多可恢复操作',
            'can_undo': history_manager.can_undo(),
            'can_redo': history_manager.can_redo()
        }), 400

    return jsonify({
        'success': True,
        'image': opencv_to_base64(img),
        'can_undo': history_manager.can_undo(),
        'can_redo': history_manager.can_redo()
    })


@app.route('/history/save', methods=['POST'])
def save_progress():
    history_manager.save_current()

    return jsonify({
        'success': True,
        'locked': True,
        'can_undo': False,
        'can_redo': False
    })


@app.route('/history/reset', methods=['POST'])
def reset_image():
    if history_manager.original_image is not None:
        original = history_manager.original_image.copy()
        history_manager.reset_to_original(original)

        return jsonify({
            'success': True,
            'image': opencv_to_base64(original),
            'can_undo': history_manager.can_undo(),
            'can_redo': history_manager.can_redo()
        })

    return jsonify({'success': False, 'error': '无原始图像'}), 400


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)