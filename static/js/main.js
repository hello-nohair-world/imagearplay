// main.js —— 完全复刻 tkinter 行为
document.addEventListener('DOMContentLoaded', function () {
    // DOM 元素
    const displayImg = document.getElementById('display-img');
    const placeholder = document.getElementById('placeholder');
    const btnLoad = document.getElementById('btn-load');
    const btnSave = document.getElementById('btn-save');
    const btnReset = document.getElementById('btn-reset');
    const btnUndo = document.getElementById('btn-undo');
    const btnRedo = document.getElementById('btn-redo');
    const btnSaveProgress = document.getElementById('btn-save-progress');
    const btnSaveBC = document.getElementById('btn-save-bc');
    const btnResetBC = document.getElementById('btn-reset-bc');
    const brightnessSlider = document.getElementById('brightness');
    const contrastSlider = document.getElementById('contrast');
    const brightnessVal = document.getElementById('brightness-val');
    const contrastVal = document.getElementById('contrast-val');

    // 状态变量
    let currentImageBase64 = null;      // 当前图像 base64
    let originalImageBase64 = null;     // 原始图像 base64
    let history = [];                   // 操作历史栈
    let historyIndex = -1;              // 当前历史位置
    const MAX_HISTORY = 20;

    // 初始化滑块监听
    brightnessSlider.oninput = updatePreview;
    contrastSlider.oninput = updatePreview;
    brightnessVal.textContent = brightnessSlider.value;
    contrastVal.textContent = contrastSlider.value.toFixed(1);

    // 通用处理函数
    async function process(action, extra = {}) {
        if (!currentImageBase64) return;
        try {
            const res = await fetch('/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action,
                    image: currentImageBase64,
                    ...extra
                })
            });
            const data = await res.json();
            if (data.success) {
                currentImageBase64 = data.image;
                displayImg.src = currentImageBase64;
                displayImg.style.display = 'block';
                placeholder.style.display = 'none';
                // 记录历史
                addToHistory(currentImageBase64, action);
            } else {
                alert(`处理失败: ${data.error}`);
            }
        } catch (e) {
            console.error(e);
            alert('网络错误，请重试');
        }
    }

    // 添加到历史栈
    function addToHistory(img, action) {
        // 如果不在末尾，截断后续
        if (historyIndex < history.length - 1) {
            history = history.slice(0, historyIndex + 1);
        }
        history.push({ img, action, ts: Date.now() });
        if (history.length > MAX_HISTORY) history.shift();
        historyIndex = history.length - 1;
        updateHistoryButtons();
    }

    // 更新按钮状态
    function updateHistoryButtons() {
        btnUndo.disabled = historyIndex <= 0;
        btnRedo.disabled = historyIndex >= history.length - 1;
        btnSave.disabled = !currentImageBase64;
        btnReset.disabled = !originalImageBase64;
        btnSaveProgress.disabled = !currentImageBase64;
    }

    // 撤回
    btnUndo.onclick = function () {
        if (historyIndex > 0) {
            historyIndex--;
            const record = history[historyIndex];
            currentImageBase64 = record.img;
            displayImg.src = currentImageBase64;
            displayImg.style.display = 'block';
            placeholder.style.display = 'none';
            updateHistoryButtons();
            alert("已撤回上一步");
        }
    };

    // 恢复
    btnRedo.onclick = function () {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            const record = history[historyIndex];
            currentImageBase64 = record.img;
            displayImg.src = currentImageBase64;
            displayImg.style.display = 'block';
            placeholder.style.display = 'none';
            updateHistoryButtons();
            alert("已恢复下一步");
        }
    };

    // 重置图像（回到原始）
    btnReset.onclick = function () {
        if (originalImageBase64) {
            currentImageBase64 = originalImageBase64;
            displayImg.src = originalImageBase64;
            displayImg.style.display = 'block';
            placeholder.style.display = 'none';
            // 清空历史，从原始开始
            history = [{ img: originalImageBase64, action: '重置', ts: Date.now() }];
 historyIndex = 0;
            updateHistoryButtons();
            alert("图像已重置");
        }
    };

    // 保存进度（当前状态存入历史，但不改变指针）
    btnSaveProgress.onclick = function () {
        if (currentImageBase64) {
            // 将当前状态覆盖历史当前位置（模拟 tk 的“保存进度”行为）
            if (historyIndex >= 0 && historyIndex < history.length) {
                history[historyIndex] = { img: currentImageBase64, action: '保存进度', ts: Date.now() };
            }
            alert("当前进度已保存！");
        }
    };

    // 保存图像（下载）
    btnSave.onclick = function () {
        if (!currentImageBase64) return;
        const link = document.createElement('a');
        link.href = currentImageBase64;
        link.download = 'processed_image.jpg';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        alert("图像已保存到本地");
    };

// === 加载图像按钮逻辑 ===
btnLoad.onclick = function () {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.style.display = 'none'; // 隐藏原生 input

    input.onchange = async function (e) {
        const file = e.target.files[0];
        if (!file) {
            console.warn("No file selected");
            return;
        }

        // 检查文件类型
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp'];
        if (!validTypes.includes(file.type)) {
            alert("仅支持 JPG/PNG/BMP 格式！");
            return;
        }

        // 读取为 base64
        const reader = new FileReader();
        reader.onload = async function (ev) {
            try {
                const imgData = ev.target.result; // "data:image/jpeg;base64,..."
                console.log("Image loaded, sending to /upload...");

                const res = await fetch('/upload', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ file: imgData })
                });

                const data = await res.json();
                console.log("Upload response:", data);

                if (data.success) {
                    // ✅ 成功：更新全局状态
                    currentImageBase64 = data.image;
                    originalImageBase64 = data.image;
                    displayImg.src = currentImageBase64;
                    displayImg.style.display = 'block';
                    placeholder.style.display = 'none';

                    // 初始化历史栈
                    history = [{ img: currentImageBase64, action: '加载', ts: Date.now() }];
                    historyIndex = 0;
                    updateHistoryButtons();

                    alert("✅ 图像加载成功！");
                } else {
                    alert(`❌ 加载失败: ${data.error || '未知错误'}`);
                    console.error("Upload error:", data);
                }
            } catch (err) {
                console.error("Upload failed:", err);
                alert(`网络错误：${err.message}`);
            }
        };

        reader.onerror = function () {
            alert("读取文件时出错，请重试。");
        };

        reader.readAsDataURL(file);
    };

    // 触发点击
    document.body.appendChild(input);
    input.click();
    document.body.removeChild(input);
};

    // 亮度/对比度预览（实时）
    function updatePreview() {
        brightnessVal.textContent = brightnessSlider.value;
        contrastVal.textContent = contrastSlider.value.toFixed(1);
        if (!currentImageBase64) return;
        // 发送临时调整（不记录历史）
        fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'adjust_preview',
                image: currentImageBase64,
                brightness: parseInt(brightnessSlider.value),
                contrast: parseFloat(contrastSlider.value)
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // 仅更新预览，不修改 currentImageBase64
                displayImg.src = data.image;
            }
        });
    }

    // 保存亮度/对比度调整（正式应用）
    btnSaveBC.onclick = function () {
        if (!currentImageBase64) return;
        process('adjust_final', {
            brightness: parseInt(brightnessSlider.value),
            contrast: parseFloat(contrastSlider.value)
        });
        alert("亮度/对比度调整已保存！");
    };

    // 重置滑块（仅滑块，不改图像）
    btnResetBC.onclick = function () {
        brightnessSlider.value = 0;
        contrastSlider.value = 1.0;
        brightnessVal.textContent = 0;
        contrastVal.textContent = "1.0";
        updatePreview(); // 触发预览回退
    };

    // 标签页切换
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hide'));
            document.getElementById(`tab-${tabId}`).classList.remove('hide');
        };
    });

    // 绑定所有 filter 按钮
    document.querySelectorAll('.filter-btn')
        .forEach(btn => btn.onclick = () => process(btn.dataset.action));

    // 初始禁用按钮
    updateHistoryButtons();
});