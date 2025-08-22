import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os


# 导入各个模块
from filters.basic_filters import BasicFilters
from filters.artistic_filters import ArtisticFilters
from filters.enhancement import ImageEnhancement
from segmentation.background_removal import BackgroundRemoval
from segmentation.object_segmentation import ObjectSegmentation
from ar_effects.face_detection import FaceDetection
from ar_effects.qr_sticker import QRSticker
from ar_effects.pose_estimation import PoseEstimation


class PhotoEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("趣味图像处理与AR交互学习平台")
        self.root.geometry("1200x800")

        # 初始化变量
        self.original_image = None
        self.current_image = None
        self.is_processing = False  # 防止滑块调整时的重复处理

        # 初始化历史记录系统
        self.history = []  # 操作历史
        self.history_index = -1  # 当前历史位置
        self.max_history = 20  # 最大历史记录数

        # 初始化各功能模块
        self.basic_filters = BasicFilters()
        self.artistic_filters = ArtisticFilters()
        self.enhancement = ImageEnhancement()
        self.bg_removal = BackgroundRemoval()
        self.selected_background_index = None
        self.background_names = []
        self.obj_segmentation = ObjectSegmentation()
        self.face_detection = FaceDetection()
        self.qr_sticker = QRSticker()
        self.pose_estimation = PoseEstimation()

        # 创建界面
        self.create_widgets()
        # 初始化按钮状态
        self.update_all_buttons()

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建顶部按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # 图像加载按钮
        load_btn = ttk.Button(button_frame, text="加载图像", command=self.load_image)
        load_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 保存按钮
        self.save_btn = ttk.Button(button_frame, text="保存图像", command=self.save_image, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 重置按钮
        self.reset_btn = ttk.Button(button_frame, text="重置图像", command=self.reset_image, state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 历史操作按钮
        history_frame = ttk.Frame(button_frame)
        history_frame.pack(side=tk.LEFT, padx=(10, 0))

        self.undo_btn = ttk.Button(history_frame, text="撤回", command=self.undo_operation, state=tk.DISABLED)
        self.undo_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.redo_btn = ttk.Button(history_frame, text="恢复", command=self.redo_operation, state=tk.DISABLED)
        self.redo_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.save_progress_btn = ttk.Button(history_frame, text="保存进度", command=self.save_progress,
                                            state=tk.DISABLED)
        self.save_progress_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 创建左右面板
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧面板 - 图像显示
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 图像显示区域
        self.image_label = ttk.Label(left_frame, text="请加载图像", anchor="center")
        self.image_label.pack(fill=tk.BOTH, expand=True)

        # 右侧面板 - 功能选择
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建标签页
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 基础滤镜标签页
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="基础滤镜")
        self.create_basic_filters_tab(basic_tab)

        # 艺术滤镜标签页
        artistic_tab = ttk.Frame(notebook)
        notebook.add(artistic_tab, text="艺术滤镜")
        self.create_artistic_filters_tab(artistic_tab)

        # 图像增强标签页
        enhancement_tab = ttk.Frame(notebook)
        notebook.add(enhancement_tab, text="图像增强")
        self.create_enhancement_tab(enhancement_tab)

        # 背景移除标签页
        bg_removal_tab = ttk.Frame(notebook)
        notebook.add(bg_removal_tab, text="背景移除")
        self.create_bg_removal_tab(bg_removal_tab)

        # 对象分割标签页
        segmentation_tab = ttk.Frame(notebook)
        notebook.add(segmentation_tab, text="对象分割")
        self.create_segmentation_tab(segmentation_tab)

        # AR效果标签页
        ar_tab = ttk.Frame(notebook)
        notebook.add(ar_tab, text="AR效果")
        self.create_ar_effects_tab(ar_tab)

    def create_basic_filters_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 灰度滤镜
        gray_btn = ttk.Button(frame, text="灰度滤镜", command=self.apply_grayscale)
        gray_btn.pack(fill=tk.X, pady=2)

        # 二值化滤镜
        binary_btn = ttk.Button(frame, text="二值化滤镜", command=self.apply_binary)
        binary_btn.pack(fill=tk.X, pady=2)

        # 反色滤镜
        invert_btn = ttk.Button(frame, text="反色滤镜", command=self.apply_invert)
        invert_btn.pack(fill=tk.X, pady=2)

        # 直方图均衡化
        hist_btn = ttk.Button(frame, text="直方图均衡化", command=self.apply_histogram_equalization)
        hist_btn.pack(fill=tk.X, pady=2)

        # 亮度对比度调整
        brightness_frame = ttk.LabelFrame(frame, text="亮度/对比度")
        brightness_frame.pack(fill=tk.X, pady=5)

        ttk.Label(brightness_frame, text="亮度:").grid(row=0, column=0, sticky=tk.W)
        self.brightness_scale = ttk.Scale(brightness_frame, from_=-100, to=100, orient=tk.HORIZONTAL,
                                          command=self.update_brightness)
        self.brightness_scale.set(0)
        self.brightness_scale.grid(row=0, column=1, sticky=tk.EW, padx=5)

        ttk.Label(brightness_frame, text="对比度:").grid(row=1, column=0, sticky=tk.W)
        self.contrast_scale = ttk.Scale(brightness_frame, from_=0.5, to=3.0, orient=tk.HORIZONTAL,
                                        command=self.update_contrast)
        self.contrast_scale.set(1.0)
        self.contrast_scale.grid(row=1, column=1, sticky=tk.EW, padx=5)

        # 保存亮度对比度调整按钮
        save_bc_btn = ttk.Button(brightness_frame, text="保存调整", command=self.save_brightness_contrast)
        save_bc_btn.grid(row=2, column=0, columnspan=2, pady=(5, 0), sticky=tk.EW)

        # 重置亮度对比度按钮 (仅重置滑块)
        reset_brightness_btn = ttk.Button(brightness_frame, text="重置滑块", command=self.reset_brightness_contrast)
        reset_brightness_btn.grid(row=3, column=0, columnspan=2, pady=(2, 0), sticky=tk.EW)

        brightness_frame.columnconfigure(1, weight=1)

    def create_artistic_filters_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 边缘检测滤镜（线描滤镜）
        edge_btn = ttk.Button(frame, text="线描滤镜", command=self.apply_edge_detection)
        edge_btn.pack(fill=tk.X, pady=2)

        # 素描滤镜
        sketch_btn = ttk.Button(frame, text="素描滤镜", command=self.apply_sketch)
        sketch_btn.pack(fill=tk.X, pady=2)

        # 卡通滤镜
        cartoon_btn = ttk.Button(frame, text="卡通滤镜", command=self.apply_cartoon)
        cartoon_btn.pack(fill=tk.X, pady=2)

        # 油画滤镜
        oil_btn = ttk.Button(frame, text="油画滤镜", command=self.apply_oil_painting)
        oil_btn.pack(fill=tk.X, pady=2)

    def create_enhancement_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 高斯模糊
        gaussian_btn = ttk.Button(frame, text="高斯模糊", command=self.apply_gaussian_blur)
        gaussian_btn.pack(fill=tk.X, pady=2)

        # 中值滤波
        median_btn = ttk.Button(frame, text="中值滤波", command=self.apply_median_blur)
        median_btn.pack(fill=tk.X, pady=2)

        # 双边滤波
        bilateral_btn = ttk.Button(frame, text="双边滤波", command=self.apply_bilateral_filter)
        bilateral_btn.pack(fill=tk.X, pady=2)

        # 锐化
        sharpen_btn = ttk.Button(frame, text="锐化", command=self.apply_sharpen)
        sharpen_btn.pack(fill=tk.X, pady=2)

        # USM锐化
        sharpen_btn = ttk.Button(frame, text="USM锐化", command=self.apply_unsharp_mask)
        sharpen_btn.pack(fill=tk.X, pady=2)

    def create_bg_removal_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 绿幕抠图
        green_screen_btn = ttk.Button(frame, text="绿幕抠图", command=self.apply_green_screen_removal)
        green_screen_btn.pack(fill=tk.X, pady=2)

        # 肤色分割
        skin_btn = ttk.Button(frame, text="肤色分割", command=self.apply_skin_segmentation)
        skin_btn.pack(fill=tk.X, pady=2)

        # 背景替换相关控件
        bg_frame = ttk.LabelFrame(frame, text="背景替换")
        bg_frame.pack(fill=tk.X, pady=5)

        # 随机背景替换
        random_bg_btn = ttk.Button(bg_frame, text="随机背景替换", command=self.replace_background_random)
        random_bg_btn.pack(fill=tk.X, pady=2)

        # 默认背景替换
        default_bg_btn = ttk.Button(bg_frame, text="默认蓝色背景", command=self.replace_background_default)
        default_bg_btn.pack(fill=tk.X, pady=2)

        # 背景选择下拉框
        bg_select_frame = ttk.Frame(bg_frame)
        bg_select_frame.pack(fill=tk.X, pady=2)

        ttk.Label(bg_select_frame, text="选择背景:").pack(side=tk.LEFT)

        self.background_combo = ttk.Combobox(bg_select_frame, state="readonly", width=15)
        self.background_combo.pack(side=tk.LEFT, padx=(5, 5))

        # 刷新背景列表按钮
        refresh_btn = ttk.Button(bg_select_frame, text="刷新", command=self.refresh_background_list, width=5)
        refresh_btn.pack(side=tk.LEFT)

        # 选择背景替换按钮
        specific_bg_btn = ttk.Button(bg_frame, text="使用选中背景", command=self.replace_background_selected)
        specific_bg_btn.pack(fill=tk.X, pady=2)

        # 初始化背景列表
        self.refresh_background_list()

    def refresh_background_list(self):
        """刷新背景列表"""
        if hasattr(self.bg_removal, 'get_background_list'):
            self.background_names = self.bg_removal.get_background_list()
            self.background_combo['values'] = self.background_names
            if self.background_names:
                self.background_combo.set("请选择背景")
            else:
                self.background_combo.set("无可用背景")

    def replace_background_random(self):
        """随机背景替换"""
        if self.current_image is not None:
            try:
                self.is_processing = True
                # 使用随机背景
                result = self.bg_removal.replace_background(
                    self.current_image,
                    background_index=None  # 让函数内部随机选择
                )
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用随机背景替换时出错: {str(e)}")

    def replace_background_default(self):
        """默认背景替换"""
        if self.current_image is not None:
            try:
                self.is_processing = True
                # 使用默认蓝色背景（不提供背景参数）
                result = self.bg_removal.replace_background(
                    self.current_image,
                    background_path=None,
                    background_index=-1  # 特殊值表示使用默认背景
                )
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用默认背景替换时出错: {str(e)}")

    def replace_background_selected(self):
        """使用选中背景替换"""
        if self.current_image is not None:
            selected = self.background_combo.get()
            if selected == "请选择背景" or selected == "无可用背景":
                messagebox.showwarning("警告", "请先选择一个背景！")
                return

            try:
                self.is_processing = True
                # 获取选中背景的索引
                if selected in self.background_names:
                    index = self.background_names.index(selected)
                    result = self.bg_removal.replace_background(
                        self.current_image,
                        background_index=index
                    )
                    self.current_image = result
                    self.add_to_history(result)
                    self.display_image(result)
                else:
                    messagebox.showwarning("警告", "选择的背景无效！")
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用选中背景替换时出错: {str(e)}")

    # 更新原有的背景替换方法
    def replace_background(self):
        """默认调用随机背景替换"""
        self.replace_background_random()

    def create_segmentation_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canny边缘分割
        canny_btn = ttk.Button(frame, text="Canny边缘分割", command=self.apply_canny_segmentation)
        canny_btn.pack(fill=tk.X, pady=2)

        # 分水岭算法
        watershed_btn = ttk.Button(frame, text="分水岭分割", command=self.apply_watershed_segmentation)
        watershed_btn.pack(fill=tk.X, pady=2)

        # 连通域分析
        connected_btn = ttk.Button(frame, text="连通域分析", command=self.apply_connected_components)
        connected_btn.pack(fill=tk.X, pady=2)

    def create_ar_effects_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- 基于 Haar 级联分类器的 AR 效果 ---
        haar_frame = ttk.LabelFrame(frame, text="Haar级联 AR效果")
        haar_frame.pack(fill=tk.X, pady=5)

        # 人脸检测
        face_btn = ttk.Button(haar_frame, text="人脸检测", command=self.detect_faces)
        face_btn.pack(fill=tk.X, pady=2)

        # 虚拟帽子
        hat_btn = ttk.Button(haar_frame, text="虚拟帽子", command=self.add_virtual_hat)
        hat_btn.pack(fill=tk.X, pady=2)

        # --- 基于 MediaPipe 的 AR 效果 ---
        mp_frame = ttk.LabelFrame(frame, text="MediaPipe AR效果")
        mp_frame.pack(fill=tk.X, pady=5)

        # 姿态估计
        pose_btn = ttk.Button(mp_frame, text="姿态估计", command=self.estimate_pose)
        pose_btn.pack(fill=tk.X, pady=2)

        # 鼻环装饰
        nose_btn = ttk.Button(mp_frame, text="鼻环装饰", command=self.add_nose_ring)
        nose_btn.pack(fill=tk.X, pady=2)

        # 墨镜特效
        sunglasses_btn = ttk.Button(mp_frame, text="墨镜特效", command=self.add_sunglasses)
        sunglasses_btn.pack(fill=tk.X, pady=2)

        # --- 基于 pyzbar 的 AR 效果 ---
        qr_frame = ttk.LabelFrame(frame, text="二维码 AR效果")
        qr_frame.pack(fill=tk.X, pady=5)

        # 二维码贴纸
        qr_btn = ttk.Button(qr_frame, text="二维码贴纸", command=self.apply_qr_sticker)
        qr_btn.pack(fill=tk.X, pady=2)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            self.original_image = cv2.imread(file_path)
            if self.original_image is not None:
                self.current_image = self.original_image.copy()
                # 清空历史记录并添加初始状态
                self.history = [self.original_image.copy()]
                self.history_index = 0
                # 重置亮度对比度滑块
                self.reset_brightness_contrast_sliders()
                self.update_all_buttons()
                self.display_image(self.current_image)
                messagebox.showinfo("成功", "图像加载成功！")
            else:
                messagebox.showerror("错误", "无法加载图像文件！")

    def save_image(self):
        if self.current_image is not None:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("BMP files", "*.bmp")]
            )
            if file_path:
                cv2.imwrite(file_path, self.current_image)
                messagebox.showinfo("成功", "图像保存成功！")
        else:
            messagebox.showwarning("警告", "没有可保存的图像！")

    def reset_image(self):
        """重置图像到原始状态"""
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            # 添加到历史记录
            self.add_to_history(self.current_image)
            # 重置亮度对比度滑块到中间位置 (与原始图像状态一致)
            self.reset_brightness_contrast_sliders()
            # 应用重置后的滑块值到显示 (确保预览也同步)
            self.apply_brightness_contrast()
            self.display_image(self.current_image)
            messagebox.showinfo("成功", "图像已重置！")
        else:
            messagebox.showwarning("警告", "没有可重置的图像！")

    def reset_brightness_contrast_sliders(self):
        """重置亮度和对比度滑块到中间位置"""
        self.brightness_scale.set(0)
        self.contrast_scale.set(1.0)

    def reset_brightness_contrast(self):
        """重置亮度和对比度效果"""
        if self.current_image is not None:
            self.reset_brightness_contrast_sliders()
            # 应用重置后的效果
            self.apply_brightness_contrast()

    def save_progress(self):
        """保存当前处理进度"""
        if self.current_image is not None:
            # 将当前状态保存到历史记录的当前索引位置
            if self.history_index >= 0:
                self.history[self.history_index] = self.current_image.copy()
                # 保存进度后，禁用撤回和恢复按钮（模拟文档编辑器行为）
                self.undo_btn.config(state=tk.DISABLED)
                self.redo_btn.config(state=tk.DISABLED)
                messagebox.showinfo("成功", "当前处理进度已保存！")
            else:
                messagebox.showwarning("警告", "没有可保存的进度！")
        else:
            messagebox.showwarning("警告", "没有可保存的图像！")

    def undo_operation(self):
        """撤回操作"""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_image = self.history[self.history_index].copy()
            self.display_image(self.current_image)
            self.update_history_buttons()
            messagebox.showinfo("成功", "已撤回上一步操作！")
        else:
            messagebox.showwarning("警告", "没有更多操作可以撤回！")

    def redo_operation(self):
        """恢复操作"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_image = self.history[self.history_index].copy()
            self.display_image(self.current_image)
            self.update_history_buttons()
            messagebox.showinfo("成功", "已恢复下一步操作！")
        else:
            messagebox.showwarning("警告", "没有更多操作可以恢复！")

    def add_to_history(self, image):
        """添加图像到历史记录"""
        if image is not None:
            # 如果当前不在历史记录的末尾，删除后面的所有记录
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]

            # 添加新图像到历史记录
            self.history.append(image.copy())
            self.history_index += 1

            # 限制历史记录数量
            if len(self.history) > self.max_history:
                self.history.pop(0)
                self.history_index -= 1

            # 更新按钮状态
            self.update_history_buttons()

    def update_history_buttons(self):
        """更新历史操作按钮状态"""
        # 更新撤回按钮
        if self.history_index > 0:
            self.undo_btn.config(state=tk.NORMAL)
        else:
            self.undo_btn.config(state=tk.DISABLED)

        # 更新恢复按钮
        if self.history_index < len(self.history) - 1:
            self.redo_btn.config(state=tk.NORMAL)
        else:
            self.redo_btn.config(state=tk.DISABLED)

        # 更新保存进度按钮
        if self.current_image is not None:
            self.save_progress_btn.config(state=tk.NORMAL)
        else:
            self.save_progress_btn.config(state=tk.DISABLED)

    def update_all_buttons(self):
        """更新所有按钮状态"""
        if self.current_image is not None:
            # 图像已加载，启用相关按钮
            self.save_btn.config(state=tk.NORMAL)
            self.reset_btn.config(state=tk.NORMAL)
            self.save_progress_btn.config(state=tk.NORMAL)
        else:
            # 没有图像，禁用相关按钮
            self.save_btn.config(state=tk.DISABLED)
            self.reset_btn.config(state=tk.DISABLED)
            self.save_progress_btn.config(state=tk.DISABLED)

        # 更新历史按钮状态
        self.update_history_buttons()

    def display_image(self, image):
        # 确保图像不为空
        if image is None:
            self.image_label.configure(text="无图像可显示", image="")
            return

        # 转换颜色空间
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 调整图像大小以适应显示区域
        h, w = rgb_image.shape[:2]
        max_height = 600
        max_width = 800

        if h > max_height or w > max_width:
            scale = min(max_height / h, max_width / w)
            new_h, new_w = int(h * scale), int(w * scale)
            rgb_image = cv2.resize(rgb_image, (new_w, new_h))

        # 转换为PIL图像并显示
        pil_image = Image.fromarray(rgb_image)
        tk_image = ImageTk.PhotoImage(pil_image)

        self.image_label.configure(image=tk_image, text="")
        self.image_label.image = tk_image  # 保持引用

    def apply_brightness_contrast(self):
        """应用当前亮度和对比度设置到预览 (不修改 self.current_image)"""
        if self.current_image is not None and not self.is_processing:
            # 使用原始的 current_image 作为基础进行调整，避免累积
            # 从历史记录中获取基础图像，以避免累积调整
            base_image = None
            if self.history and 0 <= self.history_index < len(self.history):
                 base_image = self.history[self.history_index].copy()
            else:
                 base_image = self.current_image # Fallback

            try:
                brightness = int(self.brightness_scale.get())
                contrast = float(self.contrast_scale.get())
                # 对基础图像应用调整
                result = self.basic_filters.brightness_contrast(
                    base_image, brightness=brightness, contrast=contrast
                )
                self.display_image(result)
            except Exception as e:
                # 如果调整出错，至少显示当前图像
                self.display_image(self.current_image)
                messagebox.showerror("错误", f"调整亮度对比度时出错: {str(e)}")

    def update_brightness(self, value):
        """亮度滑块变化时调用"""
        if self.current_image is not None and not self.is_processing:
            self.apply_brightness_contrast()

    def update_contrast(self, value):
        """对比度滑块变化时调用"""
        if self.current_image is not None and not self.is_processing:
            self.apply_brightness_contrast()

    def save_brightness_contrast(self):
        """保存当前亮度和对比度调整效果"""
        if self.current_image is not None:
            try:
                self.is_processing = True
                brightness = int(self.brightness_scale.get())
                contrast = float(self.contrast_scale.get())
                # 应用调整到当前图像
                result = self.basic_filters.brightness_contrast(
                    self.current_image, brightness=brightness, contrast=contrast
                )
                self.current_image = result
                # 添加到历史记录
                self.add_to_history(result)
                # 注意：不重置滑块，保持当前调整值，方便继续微调
                self.display_image(result)
                messagebox.showinfo("成功", "亮度/对比度调整已保存！")
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"保存亮度/对比度调整时出错: {str(e)}")
        else:
             messagebox.showwarning("警告", "没有可调整的图像！")

    def reset_brightness_contrast_sliders(self):
        """重置亮度和对比度滑块到中间位置"""
        self.brightness_scale.set(0)
        self.contrast_scale.set(1.0)

    def reset_brightness_contrast(self):
        """重置亮度和对比度效果 (仅重置滑块和预览)"""
        if self.current_image is not None:
            self.reset_brightness_contrast_sliders()
            # 应用重置后的效果到预览
            self.apply_brightness_contrast()

    # 基础滤镜方法
    def apply_grayscale(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.basic_filters.grayscale(self.current_image)
                result_bgr = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
                self.current_image = result_bgr
                self.add_to_history(result_bgr)
                self.display_image(result_bgr)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用灰度滤镜时出错: {str(e)}")

    def apply_binary(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.basic_filters.binary(self.current_image)
                result_bgr = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
                self.current_image = result_bgr
                self.add_to_history(result_bgr)
                self.display_image(result_bgr)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用二值化滤镜时出错: {str(e)}")

    def apply_invert(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.basic_filters.invert(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用反色滤镜时出错: {str(e)}")

    def apply_histogram_equalization(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.basic_filters.histogram_equalization(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用直方图均衡化时出错: {str(e)}")

    # 艺术滤镜方法
    def apply_edge_detection(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.artistic_filters.edge_detection(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用边缘检测时出错: {str(e)}")

    def apply_sketch(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.artistic_filters.sketch_filter(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用素描滤镜时出错: {str(e)}")

    def apply_cartoon(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.artistic_filters.cartoon_filter(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用卡通滤镜时出错: {str(e)}")

    def apply_oil_painting(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.artistic_filters.oil_painting(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用油画滤镜时出错: {str(e)}")

    # 图像增强方法
    def apply_gaussian_blur(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.enhancement.gaussian_blur(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用高斯模糊时出错: {str(e)}")

    def apply_median_blur(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.enhancement.median_blur(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用中值滤波时出错: {str(e)}")

    def apply_bilateral_filter(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.enhancement.bilateral_filter(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用双边滤波时出错: {str(e)}")

    def apply_sharpen(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.enhancement.sharpen(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用锐化时出错: {str(e)}")


    def apply_unsharp_mask(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.enhancement.unsharp_mask(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用锐化时出错: {str(e)}")

    # 背景移除方法
    def apply_green_screen_removal(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result, mask = self.bg_removal.green_screen_removal(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用绿幕抠图时出错: {str(e)}")

    def apply_skin_segmentation(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result, mask = self.bg_removal.skin_segmentation(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用肤色分割时出错: {str(e)}")

    def replace_background(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                # 创建一个简单的蓝色背景
                result = self.bg_removal.replace_background(
                    self.current_image,
                    background_path=None  # 使用默认背景
                )
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用背景替换时出错: {str(e)}")

    # 对象分割方法
    def apply_canny_segmentation(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.obj_segmentation.canny_edge_segmentation(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用Canny边缘分割时出错: {str(e)}")

    def apply_watershed_segmentation(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.obj_segmentation.watershed_segmentation(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用分水岭分割时出错: {str(e)}")

    def apply_connected_components(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.obj_segmentation.connected_components(self.current_image)
                # 转换为BGR格式以便显示
                if len(result.shape) == 3 and result.shape[2] == 3:
                    self.current_image = result
                else:
                    self.current_image = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
                self.add_to_history(self.current_image)
                self.display_image(self.current_image)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用连通域分析时出错: {str(e)}")

    # AR效果方法
    def detect_faces(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result, faces = self.face_detection.detect_faces(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                messagebox.showinfo("人脸检测", f"检测到 {len(faces)} 张人脸")
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用人脸检测时出错: {str(e)}")

    def apply_qr_sticker(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.qr_sticker.add_sticker_on_qr(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用二维码贴纸时出错: {str(e)}")

    def estimate_pose(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.pose_estimation.estimate_pose(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用姿态估计时出错: {str(e)}")

    def add_virtual_hat(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.face_detection.add_virtual_hat(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用虚拟帽子时出错: {str(e)}")

    def add_nose_ring(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.pose_estimation.add_nose_ring(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用鼻环装饰时出错: {str(e)}")

    # 添加新的墨镜特效方法
    def add_sunglasses(self):
        if self.current_image is not None:
            try:
                self.is_processing = True
                result = self.pose_estimation.add_sunglasses(self.current_image)
                self.current_image = result
                self.add_to_history(result)
                self.display_image(result)
                self.is_processing = False
            except Exception as e:
                self.is_processing = False
                messagebox.showerror("错误", f"应用墨镜特效时出错: {str(e)}")

# 创建必要的目录
def create_directories():
    directories = [
        "assets/images",
        "assets/stickers",
        "assets/backgrounds"
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建目录: {directory}")


# 运行应用程序
if __name__ == "__main__":
    # 创建必要的目录
    create_directories()

    root = tk.Tk()
    app = PhotoEditorApp(root)
    root.mainloop()
