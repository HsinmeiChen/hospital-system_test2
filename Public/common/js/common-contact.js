// ========================================
// 聯絡表單 AJAX 提交與驗證碼共用模組
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

function initCommonContactForm(options = {}) {
    const formId = options.formId || 'contactForm';
    // 允許從全域變數讀取配置 (為了與原來的架構兼容)
    const formConfig = window[options.configName || 'HEALTH_CONTACT_CONFIG'] || window.HEALTH_CONTACT_CONFIG || {};
    const refreshCaptchaUrl = formConfig.refreshCaptchaUrl || '/api/captcha/refresh/';
    const captchaImageUrl = formConfig.captchaImageUrl || '/api/captcha/image/';
    const expiryTime = options.expiryTime || 120; // 預設 2 分鐘 (120秒)

    // 檢查是否有表單提交成功的標記
    if (sessionStorage.getItem('contactSubmitted') === 'true') {
        const message = sessionStorage.getItem('contactMessage') || '您的訊息已成功送出，感謝您的聯繫！';
        sessionStorage.removeItem('contactSubmitted');
        sessionStorage.removeItem('contactMessage');
        
        // 顯示成功提示
        alert(message);
        
        // 平滑滾動到聯絡表單區域
        setTimeout(() => {
            const contactSection = document.getElementById('contact-area') || document.querySelector('.contact-form');
            if (contactSection) {
                contactSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);
    }
    
    const refreshBtn = document.getElementById('refresh-captcha-btn');
    const captchaImage = document.getElementById('captcha-image');
    let captchaInput = document.querySelector(`#${formId} input[name="captcha"]`) || 
                       document.querySelector('input[name="captcha"]') ||
                       document.querySelector('input[type="text"][placeholder*="驗證碼"]');
    const captchaTimer = document.getElementById('captcha-timer');
    
    let countdownInterval;

    function startCountdown() {
        // 重新獲取驗證碼輸入框
        captchaInput = document.querySelector(`#${formId} input[name="captcha"]`) || 
                      document.querySelector('input[name="captcha"]') ||
                      document.querySelector('input[type="text"][placeholder*="驗證碼"]');
        
        // 隱藏倒數計時提示元件
        if (captchaTimer) {
            captchaTimer.style.display = 'none';
        }
        
        if (captchaInput) {
            captchaInput.placeholder = '請輸入5位數字驗證碼';
            captchaInput.disabled = false;
            captchaInput.readOnly = false;
            captchaInput.style.cursor = '';
            captchaInput.style.backgroundColor = '';
        }
        
        if (captchaImage) {
            captchaImage.style.opacity = '1';
        }
    }

    // 刷新驗證碼圖片
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            this.style.transform = 'rotate(360deg)';
            setTimeout(() => this.style.transform = '', 300);
            
            // 隱藏錯誤提示訊息
            const captchaError = document.getElementById('contact-captcha-error') || 
                                document.querySelector(`#${formId} .captcha-error`);
            if (captchaError) {
                captchaError.textContent = '';
                captchaError.style.display = 'none';
            }
            
            fetch(refreshCaptchaUrl)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('HTTP error! status: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success === false) {
                        alert(data.message || '刷新次數過多，請稍後再試');
                        return;
                    }
                    
                    if (captchaImage) {
                        captchaImage.src = data.captcha_url || (captchaImageUrl + "?t=" + data.timestamp);
                    }
                    
                    if (captchaInput) {
                        captchaInput.value = '';
                    }
                    startCountdown();
                })
                .catch(error => {
                    console.error('刷新驗證碼失敗:', error);
                    alert('無法刷新驗證碼，請稍後再試');
                });
        });
    }

    startCountdown();
    
    // 聯絡表單 AJAX 提交
    const contactForm = document.getElementById(formId);
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitBtn = document.querySelector(`#${formId} button[type="submit"]`) || 
                             document.getElementById('contact-submit-btn');
            
            const captchaError = document.getElementById('contact-captcha-error') || 
                                document.querySelector(`#${formId} .captcha-error`);
            
            if (captchaError) {
                captchaError.textContent = '';
                captchaError.style.display = 'none';
            }
            
            if (captchaInput && captchaInput.readOnly) {
                alert('驗證碼已失效，請點擊刷新圖示重新取得驗證碼');
                if (refreshBtn) {
                    refreshBtn.focus();
                }
                return false;
            }
            
            // 禁用提交按鈕避免重複提交
            let originalText = '送出';
            if (submitBtn) {
                submitBtn.disabled = true;
                originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '送出中...';
            }
            
            const formData = new FormData(contactForm);
            
            // 使用 fetch API 發送 AJAX 請求
            fetch(contactForm.action || window.location.href, {
                method: 'POST',
                credentials: 'include', // 強制傳輸 cookie
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    sessionStorage.setItem('contactSubmitted', 'true');
                    sessionStorage.setItem('contactMessage', data.message || '您的訊息已成功送出，感謝您的聯繫！');
                    window.location.reload();
                } else {
                    if (data.errors) {
                        if (data.errors.captcha) {
                            if (captchaError) {
                                captchaError.textContent = data.errors.captcha;
                                captchaError.style.display = 'block';
                            }
                        } else {
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
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
            });
        });
    }
}
