// static/js/main.js
document.addEventListener('DOMContentLoaded', function () {
    const displayImg = document.getElementById('display-img');
    const placeholder = document.getElementById('placeholder');
    const loader = document.getElementById('loader');
    const imgStatus = document.getElementById('img-status');
    const imgDimensions = document.getElementById('img-dimensions');

    // 按钮元素
    const btnLoad = document.getElementById('btn-load');
    const btnSaveImage = document.getElementById('btn-save-image');
    const btnReset = document.getElementById('btn-reset');
    const btnUndo = document.getElementById('btn-undo');
    const btnRedo = document.getElementById('btn-redo');
    const btnSaveProgress = document.getElementById('btn-save-progress');
    const btnSaveBC = document.getElementById('btn-save-bc');
    const btnResetBC = document.getElementById('btn-reset-bc');

    // 背景替换按钮
    const btnBgRandom = document.getElementById('btn-bg-random');
    const btnBgDefault = document.getElementById('btn-bg-default');
    const btnBgSelected = document.getElementById('btn-bg-selected');
    const btnRefreshBg = document.getElementById('btn-refresh-bg');
    const backgroundSelect = document.getElementById('background-select');

    // 滑块
    const brightnessSlider = document.getElementById('brightness');
    const contrastSlider = document.getElementById('contrast');
    const brightnessVal = document.getElementById('brightness-val');
    const contrastVal = document.getElementById('contrast-val');

    // 日志面板元素
    const logPanel = document.getElementById('log-panel');
    const logContent = document.getElementById('log-content');
    const btnMinimizeLog = document.getElementById('btn-minimize-log');
    const btnClearLog = document.getElementById('btn-clear-log');

    let currentImageBase64 = null;
    let originalImageBase64 = null;
    let isProcessing = false;
    let imageWidth = 0;
    let imageHeight = 0;
    let logStartTime = Date.now();
    let previewTimeoutId = null;

    // ===== Toast 通知系统 =====
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            'success': '<i class="fa-solid fa-circle-check" style="color:#10b981;font-size:1.1rem"></i>',
            'error': '<i class="fa-solid fa-circle-exclamation" style="color:#ef4444;font-size:1.1rem"></i>',
            'warning': '<i class="fa-solid fa-triangle-exclamation" style="color:#f59e0b;font-size:1.1rem"></i>',
            'info': '<i class="fa-solid fa-circle-info" style="color:#3b82f6;font-size:1.1rem"></i>'
        };

        toast.innerHTML = `${icons[type] || icons.success}<span>${message}</span>`;
        container.appendChild(toast);

        // 3 秒后自动移除
        setTimeout(() => {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }, 3000);

        // 限制最多显示 5 个 Toast
        const toasts = container.querySelectorAll('.toast');
        if (toasts.length > 5) {
            toasts[0].classList.add('removing');
            setTimeout(() => toasts[0].remove(), 300);
        }
    }

    // ===== 日志系统 =====
    function getTimestamp() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        return `[${hours}:${minutes}:${seconds}]`;
    }

    function getElapsedTime() {
        const elapsed = Math.floor((Date.now() - logStartTime) / 1000);
        const mins = Math.floor(elapsed / 60);
        const secs = elapsed % 60;
        return `${mins}m ${secs}s`;
    }

    function addLog(message, type = 'info') {
        if (!logContent) return;
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.innerHTML = `
            <span class="log-time">${getTimestamp()}</span>
            <span class="log-message">${message}</span>
        `;
        logContent.appendChild(entry);
        // 自动滚动到底部
        logContent.scrollTop = logContent.scrollHeight;
        // 限制日志条目数量（最多 100 条）
        const entries = logContent.querySelectorAll('.log-entry');
        if (entries.length > 100) {
            entries[0].remove();
        }
    }

    function clearLog() {
        if (!logContent) return;
        logContent.innerHTML = '';
        addLog('日志已清空', 'info');
    }

    // 日志面板最小化/展开
    if (btnMinimizeLog && logPanel) {
        btnMinimizeLog.onclick = function() {
            logPanel.classList.toggle('minimized');
            const icon = btnMinimizeLog.querySelector('i');
            if (logPanel.classList.contains('minimized')) {
                icon.classList.remove('fa-minus');
                icon.classList.add('fa-plus');
            } else {
                icon.classList.remove('fa-plus');
                icon.classList.add('fa-minus');
            }
        };
    }

    // 清空日志
    if (btnClearLog) {
        btnClearLog.onclick = function(e) {
            e.stopPropagation();
            clearLog();
        };
    }

    // 点击日志头部也可以切换最小化
    if (logPanel && logPanel.querySelector('.log-header')) {
        logPanel.querySelector('.log-header').onclick = function() {
            if (btnMinimizeLog) btnMinimizeLog.click();
        };
    }

    // 获取操作名称
    function getActionName(action) {
        const actionMap = {
            'grayscale': '灰度处理',
            'binary': '二值化',
            'invert': '反色',
            'histogram_equalization': '直方图均衡化',
            'adjust_final': '亮度/对比度调整',
            'edge_detection': '边缘检测',
            'sketch': '素描滤镜',
            'cartoon': '卡通滤镜',
            'oil_painting': '油画滤镜',
            'gaussian_blur': '高斯模糊',
            'median_blur': '中值滤波',
            'bilateral_filter': '双边滤波',
            'sharpen': '锐化',
            'unsharp_mask': 'USM 锐化',
            'green_screen_removal': '绿幕抠图',
            'skin_segmentation': '肤色分割',
            'replace_background': '背景替换',
            'canny_segmentation': 'Canny 边缘分割',
            'watershed_segmentation': '分水岭分割',
            'connected_components': '连通域分析',
            'detect_faces': '人脸检测',
            'add_virtual_hat': '虚拟帽子',
            'apply_qr_sticker': '二维码贴纸',
            'estimate_pose': '姿态估计',
            'add_nose_ring': '鼻环装饰',
            'add_sunglasses': '墨镜特效',
            'replace_background_random': '随机背景',
            'replace_background_default': '默认背景',
            'replace_background_selected': '选择背景'
        };
        return actionMap[action] || action;
    }

    // ===== 加载状态管理 =====
    function setLoading(loading) {
        isProcessing = loading;
        if (loading) {
            loader.classList.add('active');
            imgStatus.textContent = '处理中...';
            document.body.style.cursor = 'wait';
            addLog('开始处理图像...', 'processing');
        } else {
            loader.classList.remove('active');
            imgStatus.textContent = '就绪';
            document.body.style.cursor = 'default';
            const elapsed = getElapsedTime();
            addLog(`处理完成 (运行时长：${elapsed})`, 'success');
        }
    }

    // ===== 按钮状态更新 =====
    function updateButtons(state = null) {
        const hasImage = !!currentImageBase64;
        btnSaveImage.disabled = !hasImage;
        btnSaveProgress.disabled = !hasImage;
        btnReset.disabled = !hasImage;
        btnBgRandom.disabled = !hasImage;
        btnBgDefault.disabled = !hasImage;
        btnBgSelected.disabled = !hasImage;

        if (state) {
            btnUndo.disabled = !state.can_undo;
            btnRedo.disabled = !state.can_redo;
        } else {
            btnUndo.disabled = !hasImage;
            btnRedo.disabled = !hasImage;
        }
    }

    // ===== 更新图像尺寸显示 =====
    function updateImageDimensions() {
        if (imageWidth > 0 && imageHeight > 0) {
            imgDimensions.textContent = `${imageWidth} × ${imageHeight}`;
        } else {
            imgDimensions.textContent = '';
        }
    }

    // ===== 预览函数（不保存到历史记录）=====
    async function previewAdjust(action, extra) {
        if (!currentImageBase64 || isProcessing) return;
        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action,
                    image: currentImageBase64,
                    preview: true,
                    ...extra
                })
            });
            const data = await response.json();
            if (data.success) {
                // 只更新显示，不更新 currentImageBase64
                displayImg.src = data.image;
                displayImg.style.display = 'block';
                placeholder.style.display = 'none';
                // 不更新按钮状态（因为历史记录没变）
            }
        } catch (e) {
            console.error('预览失败:', e);
        }
    }

    function debouncedPreview(action, extra) {
        if (previewTimeoutId) clearTimeout(previewTimeoutId);
        previewTimeoutId = setTimeout(() => {
            previewAdjust(action, extra);
        }, 150);
    }

    // ===== 通用处理函数 =====
    async function process(action, extra = {}) {
        if (!currentImageBase64 || isProcessing) return;
        setLoading(true);
        try {
            const actionName = getActionName(action);
            addLog(`执行操作：${actionName}`, 'processing');

            const startTime = performance.now();
            const response = await fetch('/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action,
                    image: currentImageBase64,
                    ...extra
                })
            });
            const data = await response.json();
            const processingTime = ((performance.now() - startTime) / 1000).toFixed(2);

            if (data.success) {
                currentImageBase64 = data.image;
                displayImg.src = currentImageBase64;
                displayImg.style.display = 'block';
                placeholder.style.display = 'none';
                updateButtons(data);
                if(action !== 'adjust_final') {
                    showToast('处理成功');
                    addLog(`${actionName} 完成 (${processingTime}s)`, 'success');
                }
            } else {
                showToast(data.error || '处理失败', 'error');
                addLog(`${actionName} 失败：${data.error}`, 'error');
            }
        } catch (e) {
            showToast('网络错误：' + e.message, 'error');
            addLog(`网络错误：${e.message}`, 'error');
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    // ===== 加载图片 =====
    btnLoad.onclick = function () {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = async function (e) {
            const file = e.target.files[0];
            if (!file) return;
            setLoading(true);
            const reader = new FileReader();
            reader.onload = async function (ev) {
                try {
                    const res = await fetch('/upload', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ file: ev.target.result })
                    });
                    const data = await res.json();
                    if (data.success) {
                        currentImageBase64 = data.image;
                        originalImageBase64 = data.image;
                        displayImg.src = currentImageBase64;
                        displayImg.style.display = 'block';
                        placeholder.style.display = 'none';
                        updateButtons(data);
                        showToast('图像加载成功');
                        addLog('图像上传成功', 'success');

                        // 获取图像尺寸
                        const tempImg = new Image();
                        tempImg.onload = function() {
                            imageWidth = tempImg.width;
                            imageHeight = tempImg.height;
                            updateImageDimensions();
                            addLog(`图像尺寸：${imageWidth}×${imageHeight}px`, 'info');
                        };
                        tempImg.src = currentImageBase64;

                        // 重置滑块
                        brightnessSlider.value = 0;
                        contrastSlider.value = 1.0;
                        brightnessVal.textContent = 0;
                        contrastVal.textContent = "1.0";

                        // 加载背景列表
                        loadBackgroundList();
                    } else {
                        showToast(data.error, 'error');
                        addLog(`图像上传失败：${data.error}`, 'error');
                    }
                } catch (err) {
                    showToast('上传失败', 'error');
                    addLog(`上传错误：${err.message}`, 'error');
                } finally {
                    setLoading(false);
                }
            };
            reader.readAsDataURL(file);
        };
        input.click();
    };

    // ===== 保存图像 =====
    btnSaveImage.onclick = async function () {
        if (!currentImageBase64 || isProcessing) return;
        setLoading(true);
        try {
            addLog('保存图像中...', 'processing');
            const res = await fetch('/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: currentImageBase64 })
            });
            const data = await res.json();
            if (data.success) {
                // 创建下载链接
                const link = document.createElement('a');
                link.href = data.download_url;
                link.download = `processed_image_${Date.now()}.jpg`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showToast('图像已准备下载');
                addLog(`图像保存成功：${data.filename}`, 'success');
            } else {
                showToast(data.error, 'error');
                addLog(`保存失败：${data.error}`, 'error');
            }
        } catch (e) {
            showToast('保存失败', 'error');
            addLog(`保存错误：${e.message}`, 'error');
        } finally {
            setLoading(false);
        }
    };

    // ===== 历史操作 =====
    btnUndo.onclick = async function () {
        if (isProcessing) return;
        setLoading(true);
        try {
            addLog('执行撤回操作', 'processing');
            const res = await fetch('/history/undo', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                currentImageBase64 = data.image;
                displayImg.src = currentImageBase64;
                updateButtons(data);
                showToast('已撤回');
                addLog('撤回成功', 'success');
            } else {
                showToast(data.error, 'error');
                addLog(`撤回失败：${data.error}`, 'error');
            }
        } catch (e) {
            showToast('操作失败', 'error');
            addLog(`撤回操作错误：${e.message}`, 'error');
        } finally {
            setLoading(false);
        }
    };

    btnRedo.onclick = async function () {
        if (isProcessing) return;
        setLoading(true);
        try {
            addLog('执行恢复操作', 'processing');
            const res = await fetch('/history/redo', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                currentImageBase64 = data.image;
                displayImg.src = currentImageBase64;
                updateButtons(data);
                showToast('已恢复');
                addLog('恢复成功', 'success');
            } else {
                showToast(data.error, 'error');
                addLog(`恢复失败：${data.error}`, 'error');
            }
        } catch (e) {
            showToast('操作失败', 'error');
            addLog(`恢复操作错误：${e.message}`, 'error');
        } finally {
            setLoading(false);
        }
    };

    btnSaveProgress.onclick = async function () {
        if (isProcessing) return;
        try {
            addLog('保存进度中...', 'processing');
            const res = await fetch('/history/save', { method: 'POST' });
            const data = await res.json();
            updateButtons(data);
            showToast('进度已保存');
            addLog('进度保存成功', 'success');
        } catch (e) {
            showToast('保存失败', 'error');
            addLog(`进度保存错误：${e.message}`, 'error');
        }
    };

    btnReset.onclick = async function () {
        if (isProcessing) return;
        setLoading(true);
        try {
            addLog('重置图像中...', 'processing');
            const res = await fetch('/history/reset', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                currentImageBase64 = data.image;
                displayImg.src = currentImageBase64;
                updateButtons(data);
                showToast('已重置为原图');
                brightnessSlider.value = 0;
                contrastSlider.value = 1.0;
                brightnessVal.textContent = 0;
                contrastVal.textContent = "1.0";
                addLog('图像重置成功', 'success');
            } else {
                showToast(data.error, 'error');
                addLog(`重置失败：${data.error}`, 'error');
            }
        } catch (e) {
            showToast('重置失败', 'error');
            addLog(`重置错误：${e.message}`, 'error');
        } finally {
            setLoading(false);
        }
    };

    // ===== 背景列表管理 =====
    async function loadBackgroundList() {
        try {
            const res = await fetch('/backgrounds/list', { method: 'GET' });
            const data = await res.json();
            if (data.success) {
                backgroundSelect.innerHTML = '<option value="">请选择背景</option>';
                data.backgrounds.forEach((bg, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = bg;
                    backgroundSelect.appendChild(option);
                });
                addLog(`加载 ${data.backgrounds.length} 个背景`, 'info');
            }
        } catch (e) {
            console.error('加载背景列表失败:', e);
            addLog(`加载背景列表失败：${e.message}`, 'error');
        }
    }

    btnRefreshBg.onclick = function () {
        loadBackgroundList();
        showToast('背景列表已刷新');
        addLog('背景列表已刷新', 'info');
    };

    // 背景替换按钮
    btnBgRandom.onclick = function () {
        process('replace_background_random');
    };

    btnBgDefault.onclick = function () {
        process('replace_background_default');
    };

    btnBgSelected.onclick = function () {
        const selectedIndex = backgroundSelect.value;
        if (selectedIndex === '') {
            showToast('请先选择一个背景', 'error');
            addLog('背景选择失败：未选择背景', 'warning');
            return;
        }
        process('replace_background_selected', { background_index: parseInt(selectedIndex) });
    };

    // ===== 亮度/对比度 =====
    brightnessSlider.oninput = function () {
        brightnessVal.textContent = this.value;
        debouncedPreview('adjust_final', {
            brightness: parseInt(this.value),
            contrast: parseFloat(contrastSlider.value)
        });
    };

    contrastSlider.oninput = function () {
        contrastVal.textContent = parseFloat(this.value).toFixed(1);
        brightnessSlider.oninput();
    };

    btnSaveBC.onclick = function () {
        process('adjust_final', {
            brightness: parseInt(brightnessSlider.value),
            contrast: parseFloat(contrastSlider.value)
        });
        showToast('亮度/对比度已应用');
        addLog('亮度/对比度调整已应用', 'success');
    };

    btnResetBC.onclick = function () {
        brightnessSlider.value = 0;
        contrastSlider.value = 1.0;
        brightnessVal.textContent = 0;
        contrastVal.textContent = "1.0";
        // 显示当前历史记录中的图像（不是预览）
        if (currentImageBase64) {
            displayImg.src = currentImageBase64;
        }
        showToast('参数已重置');
        addLog('亮度/对比度参数已重置', 'info');
    };

    // ===== 标签页切换 =====
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`tab-${tabId}`).classList.add('active');
            addLog(`切换到 ${btn.textContent.trim()} 标签页`, 'info');
        };
    });

    // ===== 滤镜按钮 =====
    document.querySelectorAll('.filter-btn[data-action]').forEach(btn => {
        btn.onclick = () => process(btn.dataset.action);
    });

    // 初始化日志
    addLog('系统初始化完成', 'success');
    addLog(`运行时间开始计时`, 'info');

    // 初始状态
    updateButtons();
});