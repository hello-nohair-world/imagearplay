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

    // 状态
    let currentImageBase64 = null;
    let originalImageBase64 = null;

    // 更新按钮状态
    function updateButtons() {
        btnSave.disabled = !currentImageBase64;
        btnReset.disabled = !originalImageBase64;
        // 检查 undo/redo 状态（通过后端）
        fetch('/history/undo', { method: 'POST' })
            .then(res => btnUndo.disabled = !res.ok || res.status === 400)
            .catch(() => btnUndo.disabled = true);
        fetch('/history/redo', { method: 'POST' })
            .then(res => btnRedo.disabled = !res.ok || res.status === 400)
            .catch(() => btnRedo.disabled = true);
        btnSaveProgress.disabled = !currentImageBase64;
    }

    // 通用处理
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
                displayImg.src = currentImageBase64;
                displayImg.style.display = 'block';
                placeholder.style.display = 'none';
                updateButtons();
            } else {
                alert(`处理失败: ${data.error}`);
            }
        } catch (e) {
            alert('网络错误');
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
            const reader = new FileReader();
            reader.onload = async function (ev) {
                try {
                    const imgData = ev.target.result;
                    const res = await fetch('/upload', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ file: imgData })
                    });
                    const data = await res.json();
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
                    }
                } catch (err) {
                    alert(`❌ 加载出错: ${err.message}`);
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
            // 🔑 重置滑块（严格复刻 main.py）
            brightnessSlider.value = 0;
            contrastSlider.value = 1.0;
            brightnessVal.textContent = 0;
            contrastVal.textContent = "1.0";
            // 应用重置效果（不触发历史）
            process('adjust_final', { brightness: 0, contrast: 1.0 });
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
            // ✅ 严格复刻 main.py：保存后立即禁用 undo/redo
            btnUndo.disabled = true;
            btnRedo.disabled = true;
            alert("💾 当前进度已保存（状态已锁定，不可撤销/恢复）！");
        } else {
            alert(data.error);
        }
    };

    // 亮度/对比度
    brightnessSlider.oninput = function () {
        brightnessVal.textContent = this.value;
        process('adjust_final', {
            brightness: parseInt(this.value),
            contrast: parseFloat(contrastSlider.value)
        });
    };
    contrastSlider.oninput = function () {
        contrastVal.textContent = this.value.toFixed(1);
        brightnessSlider.oninput();
    };

    btnSaveBC.onclick = function () {
        process('adjust_final', {
            brightness: parseInt(brightnessSlider.value),
            contrast: parseFloat(contrastSlider.value)
        });
        alert("✅ 亮度/对比度已保存！");
    };

    btnResetBC.onclick = function () {
        brightnessSlider.value = 0;
        contrastSlider.value = 1.0;
        brightnessVal.textContent = 0;
        contrastVal.textContent = "1.0";
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

    // 滤镜按钮
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.onclick = () => process(btn.dataset.action);
    });

    // 初始
    updateButtons();
});