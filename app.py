# app.py
import os
import uuid
import base64
from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
from PIL import Image
import io

# --- 假设您原有的图像处理模块路径如下 ---
# 请确保 filters/, segmentation/, ar_effects/ 等文件夹及其模块存在于项目根目录下
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
    print(f"Error importing modules: {e}")
    print("请确保您原有的 filters/, segmentation/, ar_effects/ 模块已放置在项目根目录下。")
    exit(1)

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'  # 生产环境请使用复杂随机密钥

# --- 配置 ---
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# 确保上传和处理目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# --- 实例化处理模块 ---
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
    """将OpenCV图像转换为base64字符串"""
    _, buffer = cv2.imencode('.jpg', image)
    img_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{img_str}"


def base64_to_opencv(img_data):
    """将base64字符串转换为OpenCV图像"""
    header, encoded = img_data.split(',', 1)
    decoded_data = base64.b64decode(encoded)
    np_data = np.frombuffer(decoded_data, np.uint8)
    image = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
    return image


# --- 路由 ---
@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json()
    if not data or 'file' not in data:
        return jsonify({'success': False, 'error': '请求中缺少 "file" 字段'}), 400

    img_data = data['file']
    if not img_data.startswith('data:image'):
        return jsonify({'success': False, 'error': '无效的图像数据格式（应为 data:image/...）'}), 400

    try:
        # 解析 base64
        header, encoded = img_data.split(',', 1)
        decoded_data = base64.b64decode(encoded)
        np_data = np.frombuffer(decoded_data, np.uint8)
        image = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({'success': False, 'error': '无法解码图像数据'}), 400

        # 保存（可选）
        filename = str(uuid.uuid4()) + '.jpg'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cv2.imwrite(filepath, image)

        # 返回 base64（注意：必须是 data:image/jpeg;base64,... 格式，与前端一致）
        _, buffer = cv2.imencode('.jpg', image)
        img_str = base64.b64encode(buffer).decode('utf-8')
        image_base64 = f"data:image/jpeg;base64,{img_str}"

        return jsonify({
            'success': True,
            'image': image_base64,
            'filename': filename
        })

    except Exception as e:
        print(f"[Upload Error] {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/process', methods=['POST'])
def process_image():
    """处理图像的各种操作"""
    data = request.get_json()
    action = data.get('action')
    img_data = data.get('image')

    if not img_data or not action:
        return jsonify({'success': False, 'error': 'Missing image or action'}), 400

    try:
        image = base64_to_opencv(img_data)
        processed_image = None

        # --- 分类处理各种操作 ---
        # 基础滤镜
        if action == 'grayscale':
            processed_image = basic_filters.grayscale(image)
            processed_image = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2BGR)
        elif action == 'binary':
            result = basic_filters.binary(image)
            processed_image = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        elif action == 'invert':
            processed_image = basic_filters.invert(image)
        elif action == 'histogram_equalization':
            processed_image = basic_filters.histogram_equalization(image)

        # 艺术滤镜
        elif action == 'edge_detection':
            processed_image = artistic_filters.edge_detection(image)
        elif action == 'sketch':
            processed_image = artistic_filters.sketch_filter(image)
        elif action == 'cartoon':
            processed_image = artistic_filters.cartoon_filter(image)
        elif action == 'oil_painting':
            processed_image = artistic_filters.oil_painting(image)

        # 图像增强
        elif action == 'gaussian_blur':
            processed_image = enhancement.gaussian_blur(image)
        elif action == 'median_blur':
            processed_image = enhancement.median_blur(image)
        elif action == 'bilateral_filter':
            processed_image = enhancement.bilateral_filter(image)
        elif action == 'sharpen':
            processed_image = enhancement.sharpen(image)
        elif action == 'unsharp_mask':
            processed_image = enhancement.unsharp_mask(image)

        # 背景移除
        elif action == 'green_screen_removal':
            processed_image, _ = bg_removal.green_screen_removal(image)
        elif action == 'skin_segmentation':
            processed_image, _ = bg_removal.skin_segmentation(image)
        elif action == 'replace_background':
            processed_image = bg_removal.replace_background(image)

        # 对象分割
        elif action == 'canny_segmentation':
            processed_image = obj_segmentation.canny_edge_segmentation(image)
        elif action == 'watershed_segmentation':
            processed_image = obj_segmentation.watershed_segmentation(image)
        elif action == 'connected_components':
            processed_image = obj_segmentation.connected_components(image)

        # AR效果
        elif action == 'detect_faces':
            processed_image, _ = face_detection.detect_faces(image)
        elif action == 'add_virtual_hat':
            processed_image = face_detection.add_virtual_hat(image)
        elif action == 'apply_qr_sticker':
            processed_image = qr_sticker.add_sticker_on_qr(image)
        elif action == 'estimate_pose':
            processed_image = pose_estimation.estimate_pose(image)
        elif action == 'add_nose_ring':
            processed_image = pose_estimation.add_nose_ring(image)
        elif action == 'add_sunglasses':
            processed_image = pose_estimation.add_sunglasses(image)

        # 亮度/对比度调整
        elif action in ['adjust_preview', 'adjust_final']:  # 'adjust_final' 用于最终应用调整
            brightness = data.get('brightness', 0)
            contrast = data.get('contrast', 1.0)
            processed_image = basic_filters.brightness_contrast(image, brightness=brightness, contrast=contrast)
        else:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'}), 400

        if processed_image is not None:
            processed_base64 = opencv_to_base64(processed_image)
            return jsonify({'success': True, 'image': processed_base64})
        else:
            return jsonify({'success': False, 'error': 'Processing failed, no image returned'})

    except Exception as e:
        print(f"Processing error: {e}")  # 记录错误日志
        return jsonify({'success': False, 'error': str(e)}), 500


# --- 启动应用 ---
if __name__ == '__main__':
    print("Starting Flask app...")
    print("Visit http://127.0.0.1:5000 to access the platform.")
    app.run(debug=True, host='127.0.0.1', port=5000)