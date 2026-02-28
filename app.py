# app.py
import os
import uuid
import base64
from flask import Flask, render_template, request, jsonify, send_file, url_for
import cv2
import numpy as np
from PIL import Image
import io

# --- 导入功能模块 ---
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


# === 历史管理器===
class HistoryManager:
    def __init__(self):
        # 存储字典而非单纯的图像，包含前景和掩码元数据
        self.history = []  # list of {'image': ndarray, 'foreground': ndarray, 'mask': ndarray}
        self.history_index = -1  # 当前指向的位置 (-1 表示无效/锁定/空)
        self.original_image = None  # 原始图
        self.max_history = 20

    def add(self, image, foreground=None, mask=None):
        """
        规则 1：添加历史记录，同时保存抠图元数据（前景/掩码）
        """
        if image is None:
            return
        # 构建历史条目
        entry = {
            'image': image.copy(),
            'foreground': foreground.copy() if foreground is not None else None,
            'mask': mask.copy() if mask is not None else None
        }

        if self.history_index == -1:
            if len(self.history) > 0:
                self.history_index = len(self.history) - 1
            else:
                self.history.append(entry)
                self.history_index = 0
            return

        # 如果在中间状态 (index < len - 1)，截断后续
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        self.history.append(entry)
        self.history_index += 1

        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self):
        """规则 2：撤回操作"""
        if self.history_index <= 0:
            return None, None, None
        self.history_index -= 1
        entry = self.history[self.history_index]
        return entry['image'].copy(), entry['foreground'].copy() if entry['foreground'] is not None else None, entry[
            'mask'].copy() if entry['mask'] is not None else None

    def redo(self):
        """规则 3：恢复操作"""
        if self.history_index < 0 or self.history_index >= len(self.history) - 1:
            return None, None, None
        self.history_index += 1
        entry = self.history[self.history_index]
        return entry['image'].copy(), entry['foreground'].copy() if entry['foreground'] is not None else None, entry[
            'mask'].copy() if entry['mask'] is not None else None

    def save_current(self):
        """
        规则 4：保存进度
        保存后清空保存点之前的历史记录，只保留当前状态作为新起点
        这样撤回操作不能越过保存点
        """
        if self.history_index >= 0 and self.history_index < len(self.history):
            # 获取当前状态的图像和元数据
            curr = self.history[self.history_index]
            # 清空历史，只保留当前状态作为新起点
            self.history = [{
                'image': curr['image'].copy(),
                'foreground': curr['foreground'].copy() if curr['foreground'] is not None else None,
                'mask': curr['mask'].copy() if curr['mask'] is not None else None
            }]
            self.history_index = 0

    def reset_to_original(self, original):
        """重置：清空历史，仅保留 original"""
        if original is not None:
            self.original_image = original.copy()
            self.history = [{
                'image': original.copy(),
                'foreground': None,
                'mask': None
            }]
            self.history_index = 0

    def get_current_meta(self):
        """获取当前历史状态的元数据（前景/掩码）"""
        if 0 <= self.history_index < len(self.history):
            return self.history[self.history_index]
        return None

    def can_undo(self):
        return self.history_index > 0

    def can_redo(self):
        if self.history_index < 0:
            return False
        return self.history_index < len(self.history) - 1
# 实例化历史管理器
history_manager = HistoryManager()


# --- 路由 ---
@app.route('/')
def index():
    return render_template('index.html')

# === 上传图像路由 ===
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
        # 获取当前历史状态的元数据（包含可能缓存的前景和掩码）
        current_state = history_manager.get_current_meta()
        cached_fg = current_state['foreground'] if current_state else None
        cached_mask = current_state['mask'] if current_state else None

        # --- 处理各种操作 ---
        if action == 'grayscale':
            res_gray = basic_filters.grayscale(image)
            result = cv2.cvtColor(res_gray, cv2.COLOR_GRAY2BGR)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'binary':
            res_gray = basic_filters.binary(image)
            result = cv2.cvtColor(res_gray, cv2.COLOR_GRAY2BGR)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'invert':
            result = basic_filters.invert(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'histogram_equalization':
            result = basic_filters.histogram_equalization(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'edge_detection':
            result = artistic_filters.edge_detection(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'sketch':
            result = artistic_filters.sketch_filter(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'cartoon':
            result = artistic_filters.cartoon_filter(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'oil_painting':
            result = artistic_filters.oil_painting(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'gaussian_blur':
            result = enhancement.gaussian_blur(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'median_blur':
            result = enhancement.median_blur(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'bilateral_filter':
            result = enhancement.bilateral_filter(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'sharpen':
            result = enhancement.sharpen(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'unsharp_mask':
            result = enhancement.unsharp_mask(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'green_screen_removal':
            fg, mask = bg_removal.green_screen_removal(image)
            result = fg
            history_manager.add(result, foreground=fg, mask=mask)
        elif action == 'skin_segmentation':
            result, mask = bg_removal.skin_segmentation(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action in ['replace_background', 'replace_background_random', 'replace_background_default',
                        'replace_background_selected']:
            # 背景替换：优先使用缓存的 fg/mask
            bg_index = None
            if action == 'replace_background_selected':
                bg_index = data.get('background_index', 0)
            elif action == 'replace_background_default':
                bg_index = -1

            # 确定使用的前景和掩码
            use_fg, use_mask = cached_fg, cached_mask
            if use_fg is None:
                # 如果没有缓存，重新抠图
                use_fg, use_mask = bg_removal.green_screen_removal(image)

            # 调用修改后的 replace_background，传入缓存数据
            result = bg_removal.replace_background(
                image=image,
                foreground=use_fg,
                mask=use_mask,
                background_index=bg_index
            )
            # 将使用的 fg/mask 继续传递到新的历史记录中
            history_manager.add(result, foreground=use_fg, mask=use_mask)
        elif action == 'canny_segmentation':
            result = obj_segmentation.canny_edge_segmentation(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'watershed_segmentation':
            result = obj_segmentation.watershed_segmentation(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'connected_components':
            result = obj_segmentation.connected_components(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'detect_faces':
            result, _ = face_detection.detect_faces(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'add_virtual_hat':
            result = face_detection.add_virtual_hat(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'apply_qr_sticker':
            result = qr_sticker.add_sticker_on_qr(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'estimate_pose':
            result = pose_estimation.estimate_pose(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'add_nose_ring':
            result = pose_estimation.add_nose_ring(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'add_sunglasses':
            result = pose_estimation.add_sunglasses(image)
            history_manager.add(result, foreground=None, mask=None)
        elif action == 'adjust_final':
            brightness = data.get('brightness', 0)
            contrast = data.get('contrast', 1.0)
            preview = data.get('preview', False)
            result = basic_filters.brightness_contrast(image, brightness=brightness, contrast=contrast)
            if not preview:
                history_manager.add(result, foreground=cached_fg, mask=cached_mask)

        if result is not None:
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
    img, fg, mask = history_manager.undo()
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
    img, fg, mask = history_manager.redo()
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
    app.run(host='127.0.0.1', port=5000)