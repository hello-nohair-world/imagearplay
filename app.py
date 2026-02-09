# app.py
import os
import uuid
import base64
from flask import Flask, render_template, request, jsonify, send_from_directory
import cv2
import numpy as np
from PIL import Image
import io

# 导入您提供的各个功能模块类
from filters.basic_filters import BasicFilters
from filters.artistic_filters import ArtisticFilters
from filters.enhancement import ImageEnhancement
from segmentation.background_removal import BackgroundRemoval
from segmentation.object_segmentation import ObjectSegmentation
from ar_effects.face_detection import FaceDetection
from ar_effects.qr_sticker import QRSticker
from ar_effects.pose_estimation import PoseEstimation

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于 session，生产环境应使用更安全的密钥

# --- 文件存储配置 ---
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# 确保上传和处理目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# --- 全局实例化处理模块 ---
basic_filters = BasicFilters()
artistic_filters = ArtisticFilters()
enhancement = ImageEnhancement()
bg_removal = BackgroundRemoval()
obj_segmentation = ObjectSegmentation()
face_detection = FaceDetection()
qr_sticker = QRSticker()
pose_estimation = PoseEstimation()


def opencv_to_base64(image):
    """将 OpenCV 图像转换为 base64 字符串"""
    _, buffer = cv2.imencode('.jpg', image)
    img_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{img_str}"


def base64_to_opencv(img_data):
    """将 base64 字符串转换为 OpenCV 图像"""
    header, encoded = img_data.split(',', 1)
    decoded_data = base64.b64decode(encoded)
    np_data = np.frombuffer(decoded_data, np.uint8)
    image = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
    return image


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_image():
    print("Request JSON:", request.get_json())
    print("Request Files:", request.files)
    data = request.get_json()
    if not data or 'file' not in data:
        return jsonify({'success': False, 'error': 'Invalid input: missing "file" in JSON'}), 400

    img_data = data['file']
    if not img_data.startswith('data:image'):
        return jsonify({'success': False, 'error': 'Invalid image data format'}), 400

    try:
        # 解析 base64 数据
        header, encoded = img_data.split(',', 1)
        decoded_data = base64.b64decode(encoded)
        np_data = np.frombuffer(decoded_data, np.uint8)
        image = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
        if image is None:
            return jsonify({'success': False, 'error': 'Failed to decode image'}), 400

        # 保存原始图像到 uploads/
        filename = str(uuid.uuid4()) + '.jpg'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cv2.imwrite(filepath, image)

        # 转为 base64 用于前端显示（可选：也可直接返回 image 变量）
        _, buffer = cv2.imencode('.jpg', image)
        img_str = base64.b64encode(buffer).decode('utf-8')
        original_base64 = f"data:image/jpeg;base64,{img_str}"

        return jsonify({
            'success': True,
            'image': original_base64,
            'filename': filename
        })

    except Exception as e:
        print(f"[Upload Error] {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/process', methods=['POST'])
def process_image():

    data = request.json
    action = data.get('action')
    img_data = data.get('image')
    filename = data.get('filename')

    if not img_data or not action:
        return jsonify({'success': False, 'error': 'Invalid input data'})

    try:
        image = base64_to_opencv(img_data)

        processed_image = None
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
        elif action == 'edge_detection':
            processed_image = artistic_filters.edge_detection(image)
        elif action == 'sketch':
            processed_image = artistic_filters.sketch_filter(image)
        elif action == 'cartoon':
            processed_image = artistic_filters.cartoon_filter(image)
        elif action == 'oil_painting':
            processed_image = artistic_filters.oil_painting(image)
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
        elif action == 'green_screen_removal':
            processed_image, _ = bg_removal.green_screen_removal(image)
        elif action == 'skin_segmentation':
            processed_image, _ = bg_removal.skin_segmentation(image)
        elif action == 'replace_background':
            processed_image = bg_removal.replace_background(image)
        elif action == 'canny_segmentation':
            processed_image = obj_segmentation.canny_edge_segmentation(image)
        elif action == 'watershed_segmentation':
            processed_image = obj_segmentation.watershed_segmentation(image)
        elif action == 'connected_components':
            result = obj_segmentation.connected_components(image)
            if len(result.shape) == 2:
                processed_image = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            else:
                processed_image = result
        elif action == 'detect_faces':
            result, faces = face_detection.detect_faces(image)
            processed_image = result
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
        elif action.startswith('adjust_'):
            # Handle brightness/contrast adjustments
            brightness = data.get('brightness', 0)
            contrast = data.get('contrast', 1.0)
            processed_image = basic_filters.brightness_contrast(image, brightness=brightness, contrast=contrast)
        else:
            return jsonify({'success': False, 'error': 'Unknown action'})

        if processed_image is not None:
            processed_base64 = opencv_to_base64(processed_image)
            return jsonify({'success': True, 'image': processed_base64})
        else:
            return jsonify({'success': False, 'error': 'Processing failed'})

    except Exception as e:
        print(f"Error processing image: {e}")  # For debugging
        return jsonify({'success': False, 'error': str(e)})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)