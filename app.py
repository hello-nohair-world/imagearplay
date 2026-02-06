import os
import cv2
import numpy as np
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

# 导入原有算法模块
from filters.basic_filters import BasicFilters
from filters.artistic_filters import ArtisticFilters
from filters.enhancement import ImageEnhancement
from segmentation.background_removal import BackgroundRemoval
from segmentation.object_segmentation import ObjectSegmentation
from ar_effects.face_detection import FaceDetection
from ar_effects.qr_sticker import QRSticker
from ar_effects.pose_estimation import PoseEstimation

# Flask初始化
app = Flask(__name__)
app.secret_key = "image_ar_play_2024"  # Session加密密钥
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PROCESSED_FOLDER'] = 'static/processed'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'bmp'}

# 创建必要目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# 初始化算法模块
basic_filters = BasicFilters()
artistic_filters = ArtisticFilters()
enhancement = ImageEnhancement()
bg_removal = BackgroundRemoval()
obj_segmentation = ObjectSegmentation()
face_detection = FaceDetection()
qr_sticker = QRSticker()
pose_estimation = PoseEstimation()

# 工具函数：检查文件格式
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# 工具函数：保存图像到指定路径
def save_image(image, path):
    if isinstance(image, np.ndarray):
        cv2.imwrite(path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    else:
        image.save(path)

# 工具函数：初始化历史记录
def init_history(original_path):
    session['history'] = [original_path]
    session['history_index'] = 0

# 工具函数：更新历史记录
def update_history(new_path):
    history = session.get('history', [])
    history_index = session.get('history_index', 0)
    # 截断redo部分的历史
    history = history[:history_index + 1]
    history.append(new_path)
    # 限制最大历史记录数
    if len(history) > 20:
        history = history[-20:]
    session['history'] = history
    session['history_index'] = len(history) - 1

# 工具函数。新增：通用静态资源路径处理函数（解决Windows分隔符问题）
def get_static_relative_path(absolute_path):
    # 先获取相对于static的相对路径（可能含\）
    rel_path = os.path.relpath(absolute_path, 'static')
    # 将反斜杠\替换为URL标准正斜杠/，适配所有系统
    return rel_path.replace('\\', '/')

# 首页路由
@app.route('/')
def index():
    img_static_path = None
    if session.get('history'):
        current_path = session['history'][session['history_index']]
        # 调用通用函数，自动处理分隔符，生成URL标准路径
        img_static_path = get_static_relative_path(current_path)
    return render_template('index.html', img_static_path=img_static_path)

# 上传图片路由
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('未选择文件')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('未选择文件')
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        # 初始化历史记录
        init_history(upload_path)
        flash('图片加载成功')
        return redirect(url_for('index'))
    else:
        flash('仅支持png/jpg/jpeg/bmp格式')
        return redirect(url_for('index'))

# 基础滤镜：灰度
@app.route('/filter/grayscale', methods=['POST'])
def apply_grayscale():
    if not session.get('history'):
        flash('请先加载图片')
        return redirect(url_for('index'))
    # 获取当前图片
    current_path = session['history'][session['history_index']]
    img = cv2.imread(current_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # 应用滤镜
    result = basic_filters.apply_grayscale(img_rgb)  # 复用原有方法
    # 保存处理后的图片
    filename = f"processed_{os.path.basename(current_path)}"
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    save_image(result, processed_path)
    # 更新历史记录
    update_history(processed_path)
    return redirect(url_for('index'))

# 基础滤镜：二值化
@app.route('/filter/binary', methods=['POST'])
def apply_binary():
    if not session.get('history'):
        flash('请先加载图片')
        return redirect(url_for('index'))
    current_path = session['history'][session['history_index']]
    img = cv2.imread(current_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = basic_filters.apply_binary(img_rgb)
    filename = f"binary_{os.path.basename(current_path)}"
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    save_image(result, processed_path)
    update_history(processed_path)
    return redirect(url_for('index'))

# 基础滤镜：反色
@app.route('/filter/invert', methods=['POST'])
def apply_invert():
    if not session.get('history'):
        flash('请先加载图片')
        return redirect(url_for('index'))
    current_path = session['history'][session['history_index']]
    img = cv2.imread(current_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = basic_filters.apply_invert(img_rgb)
    filename = f"invert_{os.path.basename(current_path)}"
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    save_image(result, processed_path)
    update_history(processed_path)
    return redirect(url_for('index'))

# 亮度/对比度调整
@app.route('/filter/brightness_contrast', methods=['POST'])
def adjust_brightness_contrast():
    if not session.get('history'):
        flash('请先加载图片')
        return redirect(url_for('index'))
    brightness = float(request.form.get('brightness', 0))
    contrast = float(request.form.get('contrast', 1.0))
    current_path = session['history'][session['history_index']]
    img = cv2.imread(current_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = basic_filters.adjust_brightness_contrast(img_rgb, brightness, contrast)
    filename = f"bc_{brightness}_{contrast}_{os.path.basename(current_path)}"
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    save_image(result, processed_path)
    update_history(processed_path)
    return redirect(url_for('index'))

# 艺术滤镜：线描（边缘检测）
@app.route('/filter/edge', methods=['POST'])
def apply_edge():
    if not session.get('history'):
        flash('请先加载图片')
        return redirect(url_for('index'))
    current_path = session['history'][session['history_index']]
    img = cv2.imread(current_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = artistic_filters.apply_edge_detection(img_rgb)
    filename = f"edge_{os.path.basename(current_path)}"
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    save_image(result, processed_path)
    update_history(processed_path)
    return redirect(url_for('index'))

# 撤销操作
@app.route('/undo', methods=['POST'])
def undo():
    history = session.get('history', [])
    history_index = session.get('history_index', 0)
    if history_index > 0:
        session['history_index'] = history_index - 1
    else:
        flash('已无撤销记录')
    return redirect(url_for('index'))

# 恢复操作
@app.route('/redo', methods=['POST'])
def redo():
    history = session.get('history', [])
    history_index = session.get('history_index', 0)
    if history_index < len(history) - 1:
        session['history_index'] = history_index + 1
    else:
        flash('已无恢复记录')
    return redirect(url_for('index'))

# 重置图片
@app.route('/reset', methods=['POST'])
def reset():
    if session.get('history'):
        init_history(session['history'][0])  # 重置到原始图片
    return redirect(url_for('index'))

# 保存图片
@app.route('/save', methods=['POST'])
def save_image_route():
    if not session.get('history'):
        flash('请先加载图片')
        return redirect(url_for('index'))
    current_path = session['history'][session['history_index']]
    # 返回文件下载响应（简化版，实际可优化下载逻辑）
    return redirect(url_for('static', filename=os.path.relpath(current_path, 'static')))

# 其他滤镜/功能可按上述模式扩展（如素描、卡通、背景移除等）

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')