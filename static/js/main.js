// static/js/main.js
document.addEventListener('DOMContentLoaded', function () {

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

    let currentImageBase64 = null;
    let originalImageBase64 = null;

    // ===== 按钮状态更新（完全由后端控制）=====
    function updateButtons(state = null) {

        btnSave.disabled = !currentImageBase64;
        btnReset.disabled = !originalImageBase64;
        btnSaveProgress.disabled = !currentImageBase64;

        if (!state) return;

        btnUndo.disabled = !state.can_undo;
        btnRedo.disabled = !state.can_redo;
    }

    // ===== 通用处理函数 =====
    async function process(action, extra = {}) {

        if (!currentImageBase64) return;

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

        } else {
            alert(data.error);
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

            const reader = new FileReader();

            reader.onload = async function (ev) {

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

                } else {
                    alert(data.error);
                }
            };

            reader.readAsDataURL(file);
        };

        input.click();
    };

    // ===== 撤回 =====
    btnUndo.onclick = async function () {

        const res = await fetch('/history/undo', { method: 'POST' });
        const data = await res.json();

        if (data.success) {

            currentImageBase64 = data.image;
            displayImg.src = currentImageBase64;

            updateButtons(data);
        } else {
            alert(data.error);
        }
    };

    // ===== 恢复 =====
    btnRedo.onclick = async function () {

        const res = await fetch('/history/redo', { method: 'POST' });
        const data = await res.json();

        if (data.success) {

            currentImageBase64 = data.image;
            displayImg.src = currentImageBase64;

            updateButtons(data);
        } else {
            alert(data.error);
        }
    };

    // ===== 保存进度 =====
    btnSaveProgress.onclick = async function () {

        const res = await fetch('/history/save', { method: 'POST' });
        const data = await res.json();

        updateButtons(data);

        alert("当前进度已保存！");
    };

    // ===== 重置 =====
    btnReset.onclick = async function () {

        const res = await fetch('/history/reset', { method: 'POST' });
        const data = await res.json();

        if (data.success) {

            currentImageBase64 = data.image;
            displayImg.src = currentImageBase64;

            updateButtons(data);
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