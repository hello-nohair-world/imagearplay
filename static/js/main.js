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

    let currentImageBase64 = null;
    let originalImageBase64 = null;
    let isProcessing = false;
    let imageWidth = 0;
    let imageHeight = 0;

    // ===== Toast 通知系统 =====
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = type === 'success' ? '<i class="fa-solid fa-check-circle" style="color:#10b981"></i>' :
                     '<i class="fa-solid fa-circle-exclamation" style="color:#ef4444"></i>';

        toast.innerHTML = `${icon}<span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ===== 加载状态管理 =====
    function setLoading(loading) {
        isProcessing = loading;
        if (loading) {
            loader.classList.add('active');
            imgStatus.textContent = '处理中...';
            document.body.style.cursor = 'wait';
        } else {
            loader.classList.remove('active');
            imgStatus.textContent = '就绪';
            document.body.style.cursor = 'default';
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

    // ===== 通用处理函数 =====
    async function process(action, extra = {}) {
        if (!currentImageBase64 || isProcessing) return;

        setLoading(true);
        try {
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

            if (data.success) {
                currentImageBase64 = data.image;
                displayImg.src = currentImageBase64;
                displayImg.style.display = 'block';
                placeholder.style.display = 'none';
                updateButtons(data);
                if(action !== 'adjust_final') {
                    showToast('处理成功');
                }
            } else {
                showToast(data.error || '处理失败', 'error');
            }
        } catch (e) {
            showToast('网络错误：' + e.message, 'error');
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

                        // 获取图像尺寸
                        const tempImg = new Image();
                        tempImg.onload = function() {
                            imageWidth = tempImg.width;
                            imageHeight = tempImg.height;
                            updateImageDimensions();
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
                    }
                } catch (err) {
                    showToast('上传失败', 'error');
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
            } else {
                showToast(data.error, 'error');
            }
        } catch (e) {
            showToast('保存失败', 'error');
        } finally {
            setLoading(false);
        }
    };

    // ===== 历史操作 =====
    btnUndo.onclick = async function () {
        if (isProcessing) return;
        setLoading(true);
        try {
            const res = await fetch('/history/undo', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                currentImageBase64 = data.image;
                displayImg.src = currentImageBase64;
                updateButtons(data);
                showToast('已撤回');
            } else {
                showToast(data.error, 'error');
            }
        } catch (e) {
            showToast('操作失败', 'error');
        } finally {
            setLoading(false);
        }
    };

    btnRedo.onclick = async function () {
        if (isProcessing) return;
        setLoading(true);
        try {
            const res = await fetch('/history/redo', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                currentImageBase64 = data.image;
                displayImg.src = currentImageBase64;
                updateButtons(data);
                showToast('已恢复');
            } else {
                showToast(data.error, 'error');
            }
        } catch (e) {
            showToast('操作失败', 'error');
        } finally {
            setLoading(false);
        }
    };

    btnSaveProgress.onclick = async function () {
        if (isProcessing) return;
        try {
            const res = await fetch('/history/save', { method: 'POST' });
            const data = await res.json();
            updateButtons(data);
            showToast('进度已保存');
        } catch (e) {
            showToast('保存失败', 'error');
        }
    };

    btnReset.onclick = async function () {
        if (isProcessing) return;
        setLoading(true);
        try {
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
            } else {
                showToast(data.error, 'error');
            }
        } catch (e) {
            showToast('重置失败', 'error');
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
            }
        } catch (e) {
            console.error('加载背景列表失败:', e);
        }
    }

    btnRefreshBg.onclick = function () {
        loadBackgroundList();
        showToast('背景列表已刷新');
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
            return;
        }
        process('replace_background_selected', { background_index: parseInt(selectedIndex) });
    };

    // ===== 亮度/对比度 =====
    let timeoutId = null;
    function debouncedProcess(action, extra) {
        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            process(action, extra);
        }, 300);
    }

    brightnessSlider.oninput = function () {
        brightnessVal.textContent = this.value;
        debouncedProcess('adjust_final', {
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
    };

    btnResetBC.onclick = function () {
        brightnessSlider.value = 0;
        contrastSlider.value = 1.0;
        brightnessVal.textContent = 0;
        contrastVal.textContent = "1.0";
        process('adjust_final', { brightness: 0, contrast: 1.0 });
        showToast('参数已重置');
    };

    // ===== 标签页切换 =====
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`tab-${tabId}`).classList.add('active');
        };
    });

    // ===== 滤镜按钮 =====
    document.querySelectorAll('.filter-btn[data-action]').forEach(btn => {
        btn.onclick = () => process(btn.dataset.action);
    });

    // 初始状态
    updateButtons();
});