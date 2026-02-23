// ========================================
// 驗證碼刷新與倒數計時 + AJAX 表單提交
// ========================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    // 檢查是否有表單提交成功的標記
    if (sessionStorage.getItem('contactSubmitted') === 'true') {
        const message = sessionStorage.getItem('contactMessage') || '您的訊息已成功送出，感謝您的聯繫！';
        sessionStorage.removeItem('contactSubmitted');
        sessionStorage.removeItem('contactMessage');
        alert(message);
    }
    
    const refreshBtn = document.getElementById('refresh-captcha-btn');
    const captchaImage = document.getElementById('captcha-image');
    let captchaInput = document.querySelector('#contactForm input[name="captcha"]') || 
                       document.querySelector('input[name="captcha"]');
    const captchaTimer = document.getElementById('captcha-timer');
    
    let expiryTime = 120; // 2 分鐘
    let countdownInterval;

    function startCountdown() {
        clearInterval(countdownInterval);
        let remaining = expiryTime;
        
        // 重新獲取驗證碼輸入框（防止 DOM 更新後丟失引用）
        captchaInput = document.querySelector('#contactForm input[name="captcha"]') || 
                      document.querySelector('input[name="captcha"]');
        
        // 檢查元素是否存在
        if (!captchaTimer || !captchaInput) {
            console.warn('驗證碼相關元素未找到');
            return;
        }
        
        // ✅ 重置為初始狀態
        captchaTimer.innerHTML = '驗證碼將於 <span id="countdown">2:00</span> 後失效';
        captchaTimer.className = 'form-text text-muted';
        captchaTimer.style.display = 'block';
        captchaInput.placeholder = '請輸入5位數字驗證碼';
        captchaInput.disabled = false;
        captchaInput.readOnly = false;
        captchaInput.style.cursor = '';
        captchaInput.style.backgroundColor = '';
        if (captchaImage) {
            captchaImage.style.opacity = '1';
        }
        
        const newCountdownEl = document.getElementById('countdown');
        
        countdownInterval = setInterval(() => {
            remaining--;
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            newCountdownEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (remaining <= 0) {
                clearInterval(countdownInterval);
                
                // 重新獲取輸入框（確保引用最新）
                const currentInput = document.querySelector('#contactForm input[name="captcha"]') || 
                                    document.querySelector('input[name="captcha"]');
                
                // 隱藏計時器
                captchaTimer.style.display = 'none';
                
                // 使用 readOnly 代替 disabled，並將失效訊息放在 placeholder
                if (currentInput) {
                    currentInput.readOnly = true;
                    currentInput.disabled = false;
                    currentInput.value = '';
                    currentInput.placeholder = '驗證碼已失效，請點擊刷新';
                    currentInput.style.cursor = 'not-allowed';
                    currentInput.style.backgroundColor = '#f5f5f5';
                }
                
                if (captchaImage) {
                    captchaImage.style.opacity = '0.5';
                }
            }
        }, 1000);
    }

    // 刷新驗證碼圖片
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            this.style.transform = 'rotate(360deg)';
            setTimeout(() => this.style.transform = '', 300);
            
            const refreshUrl = '/breast-care-center/api/breast-refresh-captcha/';
            const imageUrl = '/breast-care-center/api/breast-captcha-image/';
            
            fetch(refreshUrl)
                .then(response => response.json())
                .then(data => {
                    if (data.success === false) {
                        // 處理速率限制錯誤
                        alert(data.message || '刷新次數過多，請稍後再試');
                        return;
                    }
                    
                    if (captchaImage) {
                        captchaImage.src = imageUrl + "?t=" + data.timestamp;
                    }
                    
                    // 重新獲取驗證碼輸入框
                    if (!captchaInput) {
                        captchaInput = document.querySelector('#contactForm input[name="captcha"]') || 
                                      document.querySelector('input[name="captcha"]');
                    }
                    
                    if (captchaInput) {
                        captchaInput.value = '';
                    }
                    startCountdown();
                })
                .catch(error => {
                    console.error('刷新驗證碼失敗:', error);
                    if (error.message.includes('429')) {
                        alert('驗證碼刷新次數過多，請等待 1 分鐘後再試');
                    } else {
                        alert('無法刷新驗證碼，請稍後再試');
                    }
                });
        });
    }

    startCountdown();
    
    // 聯絡表單 AJAX 提交
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('contact-submit-btn');
            const captchaError = document.getElementById('contact-captcha-error');
            
            // 檢查驗證碼輸入框狀態
            const captchaInput = document.querySelector('#contactForm input[name="captcha"]');
            
            if (captchaInput && captchaInput.readOnly) {
                alert('驗證碼已失效，請點擊刷新圖示重新取得驗證碼');
                if (refreshBtn) {
                    refreshBtn.focus();
                }
                return false;
            }
            
            // 禁用提交按鈕避免重複提交
            submitBtn.disabled = true;
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '送出中...';
            
            const formData = new FormData(contactForm);
            
            // 使用 fetch API 發送 AJAX 請求
            fetch(contactForm.action || window.location.href, {
                method: 'POST',
                credentials: 'include', // 強制傳輸 cookie
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 儲存成功訊息到 sessionStorage
                    sessionStorage.setItem('contactSubmitted', 'true');
                    sessionStorage.setItem('contactMessage', data.message || '您的訊息已成功送出，感謝您的聯繫！');
                    
                    // 重新整理頁面
                    window.location.reload();
                } else {
                    // 顯示錯誤訊息
                    if (data.errors) {
                        if (data.errors.captcha) {
                            if (captchaError) {
                                captchaError.textContent = data.errors.captcha;
                                captchaError.style.display = 'block';
                            }
                            
                            // 刷新驗證碼
                            if (refreshBtn) {
                                refreshBtn.click();
                            }
                        } else {
                            // 顯示其他錯誤
                            let errorMsg = data.message || '送出失敗，請檢查您的輸入並重試。';
                            if (Object.keys(data.errors).length > 0) {
                                errorMsg += '\n';
                                for (let field in data.errors) {
                                    errorMsg += '\n' + data.errors[field];
                                }
                            }
                            alert(errorMsg);
                        }
                    } else {
                        alert(data.message || '送出失敗，請稍後再試。');
                    }
                }
            })
            .catch(error => {
                console.error('送出錯誤:', error);
                alert('網路錯誤，請檢查您的網路連接後再試。');
            })
            .finally(() => {
                // 重新啟用提交按鈕
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            });
        });
    }
});