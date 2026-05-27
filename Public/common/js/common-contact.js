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
    
    const contactForm = document.getElementById(formId);
    const refreshBtn = document.getElementById('refresh-captcha-btn');
    const captchaImage = document.getElementById('captcha-image') || document.getElementById('captcha-img');
    let captchaInput = document.querySelector(`#${formId} input[name="captcha_1"]`) || 
                       document.querySelector(`#${formId} input[name="captcha"]`) || 
                       document.querySelector('input[name="captcha_1"]') ||
                       document.querySelector('input[name="captcha"]') ||
                       document.querySelector('input[type="text"][placeholder*="驗證碼"]');
    
    let countdownInterval;

    function startCountdown() {
        if (countdownInterval) {
            clearInterval(countdownInterval);
        }

        // 重新獲取驗證碼輸入框
        captchaInput = document.querySelector(`#${formId} input[name="captcha_1"]`) || 
                       document.querySelector(`#${formId} input[name="captcha"]`) || 
                       document.querySelector('input[name="captcha_1"]') ||
                       document.querySelector('input[name="captcha"]') ||
                       document.querySelector('input[type="text"][placeholder*="驗證碼"]');
        
        const countdownSpan = document.getElementById('countdown') || document.querySelector(`#${formId} #countdown`);
        const timerContainer = document.getElementById('captcha-timer') || document.querySelector(`#${formId} #captcha-timer`);
        
        if (captchaInput) {
            captchaInput.placeholder = '請輸入5位數字驗證碼';
            captchaInput.disabled = false;
            captchaInput.readOnly = false;
            captchaInput.style.cursor = '';
            captchaInput.style.backgroundColor = '';
            captchaInput.classList.remove('is-invalid', 'is-valid');
        }
        
        if (captchaImage) {
            captchaImage.style.opacity = '1';
        }

        const captchaError = document.getElementById('contact-captcha-error') || 
                            document.querySelector(`#${formId} .captcha-error`) ||
                            document.querySelector(`#${formId} .captcha-feedback`);
        if (captchaError) {
            captchaError.textContent = '';
            captchaError.style.display = 'none';
            captchaError.classList.add('d-none');
        }

        let secondsRemaining = expiryTime;

        function updateTimerDisplay() {
            if (secondsRemaining <= 0) {
                clearInterval(countdownInterval);
                if (timerContainer) {
                    timerContainer.style.display = 'none';
                }
                if (captchaInput) {
                    captchaInput.readOnly = true;
                    captchaInput.placeholder = '驗證碼已失效，請點擊刷新圖示';
                    captchaInput.style.cursor = 'not-allowed';
                    captchaInput.style.backgroundColor = '#e9ecef';
                    
                    if (contactForm && contactForm.dataset.submittedOnce === 'true') {
                        captchaInput.classList.remove('is-valid');
                        captchaInput.classList.add('is-invalid');
                        if (captchaError) {
                            captchaError.textContent = '驗證碼已過期，請重新輸入';
                            captchaError.style.display = 'block';
                            captchaError.classList.remove('d-none');
                        }
                    }
                }
                if (captchaImage) {
                    captchaImage.style.opacity = '0.3';
                }
            } else {
                if (timerContainer) {
                    timerContainer.style.display = 'block';
                    timerContainer.classList.remove('d-none');
                }
                if (countdownSpan) {
                    const minutes = Math.floor(secondsRemaining / 60);
                    const seconds = secondsRemaining % 60;
                    countdownSpan.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                }
                secondsRemaining--;
            }
        }

        updateTimerDisplay();
        countdownInterval = setInterval(updateTimerDisplay, 1000);
    }

    // 刷新驗證碼圖片
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            this.style.transform = 'rotate(360deg)';
            setTimeout(() => this.style.transform = '', 300);
            
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

    if (captchaImage) {
        captchaImage.addEventListener('click', function() {
            if (refreshBtn) {
                refreshBtn.click();
            }
        });
    }

    startCountdown();
    
    // 監聽與驗證邏輯
    if (contactForm) {
        contactForm.dataset.submittedOnce = 'false';

        // 取得欄位對應的提示訊息元素
        function getFeedbackElement(input) {
            let feedback = input.nextElementSibling;
            while (feedback && !feedback.classList.contains('invalid-feedback') && !feedback.classList.contains('errorlist') && !feedback.classList.contains('captcha-feedback')) {
                feedback = feedback.nextElementSibling;
            }
            if (!feedback) {
                feedback = input.parentNode.querySelector('.invalid-feedback') || 
                           input.parentNode.querySelector('.errorlist') ||
                           input.parentNode.querySelector('.captcha-feedback') ||
                           document.getElementById('contact-captcha-error');
            }
            if (!feedback && (input.name === 'captcha' || input.name === 'captcha_1')) {
                const container = input.closest('.form-group') || input.closest('.form-section') || input.closest('form');
                if (container) {
                    feedback = container.querySelector('.captcha-feedback') || 
                               container.querySelector('.invalid-feedback') || 
                               container.querySelector('.errorlist');
                }
            }
            return feedback;
        }

        // 驗證單一欄位
        function validateField(input) {
            if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button' || input.type === 'reset') {
                return true;
            }
            if (input.type === 'radio') {
                return true; // 獨立於 validateForm 處理
            }

            let isValid = true;
            let errorMessage = '';

            // 尋找對應的提示訊息元素
            let feedback = getFeedbackElement(input);

            // 保存原始錯誤訊息（若無）
            if (feedback && !feedback.dataset.originalText) {
                feedback.dataset.originalText = feedback.textContent.trim();
            }

            // 1. 驗證碼獨立驗證
            if (input.name === 'captcha' || input.name === 'captcha_1') {
                const val = input.value.trim();
                if (input.readOnly) {
                    isValid = false;
                    errorMessage = '驗證碼已過期，請重新輸入';
                } else if (!val) {
                    isValid = false;
                    errorMessage = '請輸入驗證碼。';
                } else if (val.length !== 5) {
                    isValid = false;
                    errorMessage = '驗證碼字數不對';
                } else if (!/^\d{5}$/.test(val)) {
                    isValid = false;
                    errorMessage = '請輸入5位數字驗證碼';
                }
            } 
            // 2. 一般欄位 HTML5 約束驗證與 E-mail 嚴格校驗
            else {
                // 如果非必填且完全未填，則為中立狀態，不顯示綠框或紅框
                if (!input.hasAttribute('required') && !input.value.trim()) {
                    input.classList.remove('is-invalid');
                    input.classList.remove('is-valid');
                    if (feedback) {
                        feedback.style.display = 'none';
                        feedback.classList.add('d-none');
                    }
                    return true;
                }

                if (input.type === 'email') {
                    const emailVal = input.value.trim();
                    // 嚴格信箱格式：要求域名部分必須有點號及 TLD (e.g., .com)
                    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
                    isValid = emailRegex.test(emailVal);
                } else {
                    isValid = input.checkValidity();
                }
                
                if (!isValid) {
                    if (input.hasAttribute('required') && !input.value.trim()) {
                        errorMessage = (feedback && feedback.dataset.originalText) || '此欄位為必填。';
                    } else {
                        errorMessage = (feedback && feedback.dataset.originalText) || '請輸入正確的 E-mail 格式。';
                    }
                }
            }

            if (isValid) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
                if (feedback) {
                    feedback.style.display = 'none';
                    feedback.classList.add('d-none');
                }
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
                if (feedback) {
                    if (errorMessage) {
                        feedback.textContent = errorMessage;
                    }
                    feedback.style.display = 'block';
                    feedback.classList.remove('d-none');
                }
            }

            return isValid;
        }

        // 驗證整張表單
        function validateForm() {
            let isFormValid = true;

            // 1. 驗證所有輸入與文字區塊
            const inputs = contactForm.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (!validateField(input)) {
                    isFormValid = false;
                }
            });

            // 2. 驗證類別 radio 群組 (針對 contact_us.html)
            const categoryRadios = contactForm.querySelectorAll('input[name="category"]');
            if (categoryRadios.length > 0) {
                const checkedRadio = contactForm.querySelector('input[name="category"]:checked');
                const categoryError = document.getElementById('category-error');
                const radioGroup = contactForm.querySelector('.modern-radio-group');
                if (!checkedRadio) {
                    isFormValid = false;
                    if (categoryError) {
                        categoryError.style.display = 'block';
                        categoryError.classList.remove('d-none');
                        categoryError.classList.add('d-block');
                    }
                    if (radioGroup) {
                        radioGroup.classList.remove('is-valid');
                        radioGroup.classList.add('is-invalid');
                    }
                } else {
                    if (categoryError) {
                        categoryError.style.display = 'none';
                        categoryError.classList.add('d-none');
                        categoryError.classList.remove('d-block');
                    }
                    if (radioGroup) {
                        radioGroup.classList.remove('is-invalid');
                        radioGroup.classList.add('is-valid');
                    }
                }
            }

            return isFormValid;
        }

        // 為每個輸入欄位綁定 input/change 監聽器
        contactForm.querySelectorAll('input, select, textarea').forEach(input => {
            const handleInputEvent = function() {
                let feedback = getFeedbackElement(this);

                if (contactForm.dataset.submittedOnce === 'true') {
                    validateField(this);
                    
                    // 如果是 radio 則連動更新 radio 群組狀態
                    if (this.type === 'radio') {
                        const checkedRadio = contactForm.querySelector('input[name="category"]:checked');
                        const categoryError = document.getElementById('category-error');
                        const radioGroup = contactForm.querySelector('.modern-radio-group');
                        if (checkedRadio) {
                            if (categoryError) {
                                categoryError.style.display = 'none';
                                categoryError.classList.add('d-none');
                            }
                            if (radioGroup) {
                                radioGroup.classList.remove('is-invalid');
                                radioGroup.classList.add('is-valid');
                            }
                        }
                    }
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.remove('is-valid');
                    if (feedback) {
                        feedback.style.display = 'none';
                        feedback.classList.add('d-none');
                    }
                }
            };
            
            input.addEventListener('input', handleInputEvent);
            input.addEventListener('change', handleInputEvent);
        });

        // 監聽重置事件
        contactForm.addEventListener('reset', function() {
            contactForm.dataset.submittedOnce = 'false';
            contactForm.querySelectorAll('.is-invalid, .is-valid').forEach(el => {
                el.classList.remove('is-invalid', 'is-valid');
            });
            contactForm.querySelectorAll('.invalid-feedback, .errorlist, .captcha-feedback').forEach(el => {
                el.style.display = 'none';
                el.classList.add('d-none');
            });
            const categoryError = document.getElementById('category-error');
            if (categoryError) {
                categoryError.style.display = 'none';
                categoryError.classList.add('d-none');
            }
            const radioGroup = contactForm.querySelector('.modern-radio-group');
            if (radioGroup) {
                radioGroup.classList.remove('is-invalid', 'is-valid');
            }
        });

        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const submitBtn = document.querySelector(`#${formId} button[type="submit"]`) || 
                             document.getElementById('contact-submit-btn') ||
                             document.getElementById('submit');
            const captchaErrorGlobal = document.getElementById('contact-captcha-error') || 
                                       document.querySelector(`#${formId} .captcha-error`);
            
            // 啟用送出後即時驗證機制
            contactForm.dataset.submittedOnce = 'true';
            
            // 執行表單驗證
            const isFormValid = validateForm();
            if (!isFormValid) {
                const firstInvalidInput = contactForm.querySelector('.is-invalid');
                if (firstInvalidInput) {
                    firstInvalidInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstInvalidInput.focus();
                }
                return false;
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
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> 送出中...';
            }
            
            const formData = new FormData(contactForm);
            
            // 使用 fetch API 發送 AJAX 請求
            fetch(contactForm.action || window.location.href, {
                method: 'POST',
                credentials: 'include', // 強制傳輸 cookie
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken') || (document.querySelector('input[name="csrfmiddlewaretoken"]') ? document.querySelector('input[name="csrfmiddlewaretoken"]').value : ''),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok && response.status !== 400 && response.status !== 403 && response.status !== 429) {
                    throw new Error('伺服器傳回錯誤代碼: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    sessionStorage.setItem('contactSubmitted', 'true');
                    sessionStorage.setItem('contactMessage', data.message || '您的訊息已成功送出，感謝您的聯繫！');
                    window.location.reload();
                } else {
                    if (data.errors) {
                        // 將錯誤訊息一一對照到各輸入欄位下方
                        let hasMapped = false;
                        for (let field in data.errors) {
                            let fieldInput = contactForm.querySelector(`[name="${field}"]`);
                            if (!fieldInput && field === 'captcha') {
                                fieldInput = contactForm.querySelector('[name="captcha_1"]') || contactForm.querySelector('[name="captcha_0"]');
                            }
                            if (fieldInput) {
                                hasMapped = true;
                                fieldInput.classList.remove('is-valid');
                                fieldInput.classList.add('is-invalid');
                                
                                let feedback = getFeedbackElement(fieldInput);
                                if (feedback) {
                                    feedback.textContent = data.errors[field];
                                    feedback.style.display = 'block';
                                    feedback.classList.remove('d-none');
                                }
                            }
                        }
                        // 如果有某些錯誤無法對照，或者都沒有對照到，則彈窗提示 general message
                        if (!hasMapped || data.message) {
                            alert(data.message || '表單填寫有誤，請檢查後再試。');
                        }
                        
                        // 滾動到第一個錯誤的位置
                        const firstInvalidInput = contactForm.querySelector('.is-invalid');
                        if (firstInvalidInput) {
                            firstInvalidInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            firstInvalidInput.focus();
                        }
                    } else {
                        alert(data.message || '送出失敗，請稍後再試。');
                    }
                }
            })
            .catch(error => {
                console.error('送出錯誤:', error);
                alert('網路錯誤或系統忙碌中，請檢查您的網路連接後再試。');
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

// ========================================
// contact_us.html 專屬邏輯 (若存在該表單則執行)
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    const contactUsForm = document.getElementById('contact_us');
    if (contactUsForm) {
        // 1. 計算剩餘字數 & 動態更新 UI
        const maxLength = 500;
        const msgus = document.getElementById('msgus');
        if (msgus) {
            msgus.addEventListener('input', function() {
                const length = this.value.length;
                const remaining = maxLength - length;
                const counter = document.getElementById('rchars');
                
                if (counter) {
                    counter.textContent = remaining;
                    if (remaining < 50) {
                        counter.classList.remove('text-theme');
                        counter.classList.add('text-danger');
                    } else {
                        counter.classList.remove('text-danger');
                        counter.classList.add('text-theme');
                    }
                }
            });
        }

        // 2. 預設帶入當下日期與時間
        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, '0');
        const dd = String(now.getDate()).padStart(2, '0');
        const hh = String(now.getHours()).padStart(2, '0');
        const min = String(now.getMinutes()).padStart(2, '0');
        
        const dateStr = `${yyyy}-${mm}-${dd}`;
        const timeStr = `${hh}:${min}`;

        const dateInput = document.getElementById('id_incident_date');
        const timeInput = document.getElementById('id_incident_time');
        if (dateInput && !dateInput.value) {
            dateInput.value = dateStr;
        }
        if (timeInput && !timeInput.value) {
            timeInput.value = timeStr;
        }

        // 3. 加上 required 與 pattern 屬性
        const idName = document.getElementById('id_name');
        if (idName) idName.required = true;
        if (msgus) msgus.required = true;
        
        const idPhone = document.getElementById('id_phone');
        if (idPhone) idPhone.setAttribute('pattern', '^\\+?\\d{8,15}$');
        
        // 尋找 Captcha 的輸入框並設為必填
        const captchaInput = document.querySelector('.modern-captcha-section input[type="text"]:not([readonly])');
        if (captchaInput) {
            captchaInput.required = true;
        }

        // 幫 Django 產生的 Input 加上 form-control class
        document.querySelectorAll('.modern-input-group input:not([type="radio"]):not([type="checkbox"]), .modern-input-group select, .modern-input-group textarea').forEach(el => {
            el.classList.add('form-control');
        });

        // 當 radio 改變時移除錯誤提示
        document.querySelectorAll('input[name="category"]').forEach(radio => {
            radio.addEventListener('change', function() {
                const error = document.getElementById('category-error');
                if (error) {
                    error.classList.remove('d-block');
                    error.classList.add('d-none');
                }
                const group = document.querySelector('.modern-radio-group');
                if (group) group.classList.remove('is-invalid');
            });
        });

        // 初始化共通聯絡表單邏輯
        initCommonContactForm({
            formId: 'contact_us'
        });
    }
});

// ========================================
// 共通聯絡表單 (#contactForm) 初始化邏輯
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        // 計算剩餘字數
        const maxLength = 500;
        const msgTextarea = contactForm.querySelector('textarea[name="message"]');
        if (msgTextarea) {
            msgTextarea.addEventListener('input', function() {
                const length = this.value.length;
                const remaining = maxLength - length;
                const counter = document.getElementById('rchars');
                
                if (counter) {
                    counter.textContent = remaining;
                    if (remaining < 50) {
                        counter.classList.remove('text-theme');
                        counter.classList.add('text-danger');
                    } else {
                        counter.classList.remove('text-danger');
                        counter.classList.add('text-theme');
                    }
                }
            });
        }

        // 為 Django 產生的 Input 加上 form-control class
        document.querySelectorAll('.modern-input-group input, .modern-input-group textarea, .modern-input-group select').forEach(el => {
            el.classList.add('form-control');
        });
        
        // 確保某些欄位為必填 (防護)
        ['id_name', 'id_phone', 'id_email', 'id_subject', 'msgus', 'id_message'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.required = true;
        });
        
        // 電話格式正規表達式
        const idPhone = document.getElementById('id_phone');
        if (idPhone) idPhone.setAttribute('pattern', '^\\+?\\d{8,15}$');
        
        // 驗證碼輸入框
        const captchaInput = document.querySelector('.modern-captcha-section input[type="text"]:not([readonly])');
        if (captchaInput) {
            captchaInput.classList.add('form-control');
            captchaInput.required = true;
        }

        // 初始化共通聯絡表單邏輯
        initCommonContactForm({ formId: 'contactForm' });
    }
});