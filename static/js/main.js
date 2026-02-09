// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    const displayImage = document.getElementById('display-image');
    const placeholderText = document.getElementById('placeholder-text');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadFileInput = document.getElementById('upload-file');
    const buttons = document.querySelectorAll('.controls button[data-action]');
    const brightnessSlider = document.getElementById('brightness-slider');
    const contrastSlider = document.getElementById('contrast-slider');
    const brightnessValue = document.getElementById('brightness-value');
    const contrastValue = document.getElementById('contrast-value');
    const adjustBtn = document.getElementById('adjust-btn');

    let currentImageBase64 = null;
    let currentFilename = null;

    // 上传图片
    uploadBtn.onclick = function() {
        const file = uploadFileInput.files[0];
        if (!file) {
            alert('请选择一张图片！');
            return;
        }
        const reader = new FileReader();
        reader.onload = function(event) {
            const imageData = event.target.result;
            fetch('/upload', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({file: imageData}),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentImageBase64 = data.image;
                    currentFilename = data.filename;
                    displayImage.src = currentImageBase64;
                    displayImage.style.display = 'block';
                    placeholderText.style.display = 'none';
                } else {
                    alert(`上传失败: ${data.error}`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('上传过程中发生错误');
            });
        };
        reader.readAsDataURL(file);
    };

    // 通用处理函数
    function processImage(action, additionalData = {}) {
        if (!currentImageBase64) {
            alert('请先上传一张图片！');
            return;
        }
        const payload = {
            action: action,
            image: currentImageBase64,
            filename: currentFilename,
            ...additionalData
        };

        fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentImageBase64 = data.image;
                displayImage.src = currentImageBase64;
            } else {
                alert(`处理失败: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('处理过程中发生错误');
        });
    }

    // 为所有带 data-action 的按钮绑定事件
    buttons.forEach(button => {
        button.onclick = function() {
            const action = this.getAttribute('data-action');
            processImage(action);
        };
    });

    // 亮度对比度滑块
    brightnessSlider.oninput = function() {
        brightnessValue.textContent = this.value;
    };
    contrastSlider.oninput = function() {
        contrastValue.textContent = this.value.toFixed(1);
    };

    adjustBtn.onclick = function() {
        processImage('adjust_manual', {
            brightness: parseInt(brightnessSlider.value),
            contrast: parseFloat(contrastSlider.value)
        });
    };
});