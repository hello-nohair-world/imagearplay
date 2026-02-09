document.addEventListener('DOMContentLoaded', function () {
    // DOM 元素（严格对应 HTML 中的 id）
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
    let currentImageBase64 = null;
    let originalImageBase64 = null;

    // 图像加载失败处理
    displayImg.onerror = function() {
        console.error("❌ 图像加载失败！src =", this.src.substring(0, 100) + "...");
        alert("图像加载失败，请检查控制台日志。");
        placeholder.style.display = 'block';
        displayImg.style.display = 'none';
    };

    // 更新按钮状态
    function updateButtons() {
        btnSave.disabled = !currentImageBase64;
        btnReset.disabled = !originalImageBase64;
        // 从后端查询状态（更准确）
        checkUndoRedoState();
    }

    // 查询 undo/redo 状态
    async function checkUndoRedoState() {
        try {
            const undoRes = await fetch('/history/undo', { method: 'POST' });
            btnUndo.disabled = !undoRes.ok || undoRes.status === 400;

            const redoRes = await fetch('/history/redo', { method: 'POST' });
            btnRedo.disabled = !redoRes.ok || redoRes.status === 400;
        } catch (e) {
            // 如果后端出错，保守禁用
            btnUndo.disabled = true;
            btnRedo.disabled = true;
        }
    }

    // 通用处理函数
    async function process(action, extra = {}) {
        if (!currentImageBase64) return;
        try {
            const res = await fetch('/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, image: currentImageBase64, ...extra })
            });
            const data = await res.json();
            if (data.success) {
                currentImageBase64 = data.image;

                // ✅ 方法1：先尝试 data URL
                displayImg.src = currentImageBase64;

                // ✅ 方法2：如果 data URL 失败，用 blob fallback
                setTimeout(() => {
                    if (displayImg.complete && !displayImg.naturalWidth) {
                        // data URL 失败，尝试 blob
                        try {
                            const byteString = atob(currentImageBase64.split(',')[1]);
                            const ab = new ArrayBuffer(byteString.length);
                            const ia = new Uint8Array(ab);
                            for (let i = 0; i < byteString.length; i++) {
                                ia[i] = byteString.charCodeAt(i);
                            }
                            const blob = new Blob([ab], { type: 'image/jpeg' });
                            displayImg.src = URL.createObjectURL(blob);
                        } catch (e) {
                            console.error("Blob fallback failed:", e);
                            placeholder.style.display = 'block';
                            displayImg.style.display = 'none';
                        }
                    }
                }, 100);
            } else {
                alert(`处理失败: ${data.error}`);
            }
        } catch (e) {
            alert('网络错误，请重试');
        }
    }

    // === 按钮事件 ===
    // 加载图像
    btnLoad.onclick = function () {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.style.display = 'none';
        input.onchange = async function (e) {
            const file = e.target.files[0];
            if (!file) return;

            const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp'];
            if (!validTypes.includes(file.type)) {
                alert("仅支持 JPG/PNG/BMP！");
                return;
            }

            const reader = new FileReader();
            reader.onload = async function (ev) {
                const imgData = ev.target.result;
                console.log("Received imgData:", imgData.substring(0, 60) + "...");

                // ✅ 强制校验：必须是 data:image/xxx;base64,...
                if (!imgData.startsWith('data:image/') || !imgData.includes(','))
                {
                    alert("❌ 无法读取图像：数据格式不正确，请重试或换一张图片。");
                    console.error("Invalid imgData format:", imgData);
                    return;
                }

                try {
                    const res = await fetch('/upload', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ file: imgData })
                    });
                    const data = await res.json();
                    console.log("Upload response:", data);

                    if (data.success) {
                        currentImageBase64 = data.image;
                        originalImageBase64 = data.image;
                        displayImg.src = currentImageBase64;
                        displayImg.style.display = 'block';
                        placeholder.style.display = 'none';
                        updateButtons();
                        alert("✅ 图像加载成功！");
                    } else {
                        alert(`❌ 加载失败: ${data.error}`);
                        console.error("Upload error:", data);
                    }
                } catch (err) {
                    alert(`网络错误: ${err.message}`);
                    console.error(err);
                }
            };
            reader.readAsDataURL(file);
        };

        document.body.appendChild(input);
        input.click();
        document.body.removeChild(input);
    };

    // 保存图像
    btnSave.onclick = function () {
        if (!currentImageBase64) return;
        const link = document.createElement('a');
        link.href = currentImageBase64;
        link.download = 'processed.jpg';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        alert("✅ 图像已保存！");
    };

    // 重置图像
    btnReset.onclick = async function () {
        if (!originalImageBase64) return;
        const res = await fetch('/history/reset', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            currentImageBase64 = data.image;
            displayImg.src = currentImageBase64;
            displayImg.style.display = 'block';
            placeholder.style.display = 'none';
            // 重置滑块
            brightnessSlider.value = 0;
            contrastSlider.value = 1.0;
            brightnessVal.textContent = 0;
            contrastVal.textContent = "1.0";
            updateButtons();
            alert("✅ 图像已重置！");
        } else {
            alert(data.error);
        }
    };

    // 撤回
    btnUndo.onclick = async function () {
        const res = await fetch('/history/undo', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            currentImageBase64 = data.image;
            displayImg.src = currentImageBase64;
            displayImg.style.display = 'block';
            placeholder.style.display = 'none';
            updateButtons();
            alert("↩ 已撤回上一步！");
        } else {
            alert(data.error);
        }
    };

    // 恢复
    btnRedo.onclick = async function () {
        const res = await fetch('/history/redo', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            currentImageBase64 = data.image;
            displayImg.src = currentImageBase64;
            displayImg.style.display = 'block';
            placeholder.style.display = 'none';
            updateButtons();
            alert("↪ 已恢复下一步！");
        } else {
            alert(data.error);
        }
    };

    // 保存进度
    btnSaveProgress.onclick = async function () {
        if (!currentImageBase64) return;
        const res = await fetch('/history/save', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            // ✅ 保存进度后，立即禁用 undo/redo
            btnUndo.disabled = true;
            btnRedo.disabled = true;
            alert("💾 当前进度已保存（当前状态已锁定，不可撤销/恢复）！");
        } else {
            alert(data.error);
        }
    };

    // 亮度/对比度滑块
    brightnessSlider.oninput = function () {
        brightnessVal.textContent = this.value;
        // 实时预览（不记录历史）
        process('adjust_final', {
            brightness: parseInt(this.value),
            contrast: parseFloat(contrastSlider.value)
        });
    };
    contrastSlider.oninput = function () {
        contrastVal.textContent = this.value.toFixed(1);
        brightnessSlider.oninput(); // 触发预览
    };

    // 保存调整
    btnSaveBC.onclick = function () {
        process('adjust_final', {
            brightness: parseInt(brightnessSlider.value),
            contrast: parseFloat(contrastSlider.value)
        });
        alert("✅ 亮度/对比度已保存！");
    };

    // 重置滑块
    btnResetBC.onclick = function () {
        brightnessSlider.value = 0;
        contrastSlider.value = 1.0;
        brightnessVal.textContent = 0;
        contrastVal.textContent = "1.0";
        // 应用重置值（但不改变图像，除非点击“保存调整”）
        process('adjust_final', { brightness: 0, contrast: 1.0 });
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
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.onclick = () => process(btn.dataset.action);
    });

    // 初始禁用按钮
    updateButtons();
});