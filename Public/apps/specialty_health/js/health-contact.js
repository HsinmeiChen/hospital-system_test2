// 驗證碼刷新與倒數計時
document.addEventListener('DOMContentLoaded', function() {
    const refreshBtn = document.getElementById('refresh-captcha-btn');
    const captchaImage = document.getElementById('captcha-image');
    const countdownEl = document.getElementById('countdown');
    const captchaInput = document.querySelector('input[name="captcha"]');
    const captchaTimer = document.getElementById('captcha-timer');
    
    let expiryTime = 60; // 1 分鐘
    let countdownInterval;

    function startCountdown() {
        clearInterval(countdownInterval);
        let remaining = expiryTime;
        
        // ✅ 重置為初始狀態
        captchaTimer.innerHTML = '驗證碼將於 <span id="countdown">1:00</span> 後失效';
        captchaTimer.className = 'form-text text-muted';
        captchaTimer.style.display = ''; // ✅ 顯示提示文字
        captchaInput.placeholder = '請輸入5位數字驗證碼';
        captchaInput.disabled = false;
        captchaInput.style.cursor = '';
        captchaImage.style.opacity = '1';
        
        const newCountdownEl = document.getElementById('countdown');
        
        countdownInterval = setInterval(() => {
            remaining--;
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            newCountdownEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (remaining <= 0) {
                clearInterval(countdownInterval);
                
                // 隱藏提示文字
                captchaTimer.style.display = 'none';
                
                // 設定 input 為禁用狀態並更改 placeholder
                captchaInput.disabled = true;
                captchaInput.placeholder = '驗證碼已失效，請重新整理或點擊刷新';
                captchaInput.value = '';
                captchaInput.style.cursor = 'not-allowed';
                captchaImage.style.opacity = '0.5';
            }
        }, 1000);
    }

    // 刷新驗證碼圖片
    refreshBtn.addEventListener('click', function() {
        this.style.transform = 'rotate(360deg)';
        setTimeout(() => this.style.transform = '', 300);
        
        const refreshUrl = (window.HEALTH_CONTACT_CONFIG && window.HEALTH_CONTACT_CONFIG.refreshCaptchaUrl) || '/specialty_health/api/refresh-captcha/';
        const imageUrl = (window.HEALTH_CONTACT_CONFIG && window.HEALTH_CONTACT_CONFIG.captchaImageUrl) || '/specialty_health/api/captcha-image/';
        fetch(refreshUrl)
            .then(response => response.json())
            .then(data => {
                // 更新圖片 src（加時間戳記避免快取）
                captchaImage.src = imageUrl + "?t=" + data.timestamp;
                captchaInput.value = '';
                startCountdown(); // 重新啟動倒數（會自動重置所有狀態）
            })
            .catch(error => {
                console.error('刷新驗證碼失敗:', error);
                alert('無法刷新驗證碼，請重新整理頁面');
            });
    });

    startCountdown();
});