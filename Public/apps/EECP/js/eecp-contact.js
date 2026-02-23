// ========================================
// 平滑滾動功能
// ========================================
function scrollToContact() {
    const contactSection = document.getElementById('contact-area');
    if (contactSection) {
        contactSection.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// ========================================
// EECP 測驗功能
// ========================================
let currentQuestionNumber = 1;
let answers = {};
let totalScore = 0;
let resultText = '';

function initQuiz() {
    // 選項點擊事件
    document.querySelectorAll('.quiz-option input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const questionNum = this.name;
            answers[questionNum] = parseInt(this.value);
            
            // 自動跳轉到下一題或結果頁
            if (currentQuestionNumber < 8) {
                setTimeout(() => {
                    nextQuestion();
                }, 300);
            } else {
                // 最後一題自動顯示結果
                setTimeout(() => {
                    showResult();
                }, 300);
            }
        });
    });
    
    // 讓整個 quiz-option 區塊可點擊
    document.querySelectorAll('.quiz-option').forEach(option => {
        option.addEventListener('click', function(e) {
            // 如果點擊的不是 input 或 label，就觸發 radio 的點擊
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'LABEL') {
                const radio = this.querySelector('input[type="radio"]');
                if (radio && !radio.checked) {
                    radio.checked = true;
                    radio.dispatchEvent(new Event('change'));
                }
            }
        });
    });
}

function nextQuestion() {
    if (currentQuestionNumber < 8) {
        document.querySelector(`.quiz-question[data-question="${currentQuestionNumber}"]`).classList.remove('active');
        currentQuestionNumber++;
        document.querySelector(`.quiz-question[data-question="${currentQuestionNumber}"]`).classList.add('active');
        updateProgress();
        
        // 重置按鈕為 disabled（自動跳轉不啟用按鈕）
        const nextBtn = document.getElementById('nextBtn' + currentQuestionNumber);
        const resultBtn = document.getElementById('resultBtn8');
        
        if (currentQuestionNumber < 8) {
            if (nextBtn) nextBtn.disabled = true;
        } else if (currentQuestionNumber === 8) {
            if (resultBtn) resultBtn.disabled = true;
        }
    }
}

function previousQuestion() {
    if (currentQuestionNumber > 1) {
        document.querySelector(`.quiz-question[data-question="${currentQuestionNumber}"]`).classList.remove('active');
        currentQuestionNumber--;
        document.querySelector(`.quiz-question[data-question="${currentQuestionNumber}"]`).classList.add('active');
        updateProgress();
        
        // 檢查當前題目是否已有答案，如果有則啟用下一題或查看結果按鈕
        const hasAnswer = answers['q' + currentQuestionNumber] !== undefined;
        const nextBtn = document.getElementById('nextBtn' + currentQuestionNumber);
        const resultBtn = document.getElementById('resultBtn8');
        
        if (currentQuestionNumber < 8) {
            if (nextBtn) nextBtn.disabled = !hasAnswer;
        } else if (currentQuestionNumber === 8) {
            if (resultBtn) resultBtn.disabled = !hasAnswer;
        }
    }
}

function updateProgress() {
    const progress = (currentQuestionNumber / 8) * 100;
    document.getElementById('currentQuestion').textContent = currentQuestionNumber;
    document.getElementById('progressBar').style.width = progress + '%';
}

function showResult() {
    // 計算總分
    totalScore = Object.values(answers).reduce((sum, val) => sum + val, 0);
    
    // 根據分數判斷風險等級
    let status, description, recommendation, riskLevel;
    
    if (totalScore <= 8) {
        status = '低風險 - 健康狀況良好';
        description = '您目前的心血管健康狀況相對良好。建議定期進行健康檢查，並保持健康的生活方式。';
        recommendation = '建議進行定期的心血管健康檢查和預防性保養。EECP 可作為預防性治療，幫助您維持和改善心血管健康。';
        riskLevel = 'low';
    } else if (totalScore <= 16) {
        status = '中等風險 - 建議進一步評估';
        description = '您可能有一些心血管相關的症狀或風險因素。建議諮詢醫療專業人士進行進一步評估。';
        recommendation = '強烈建議進行心血管健康評估。EECP 是一種安全、有效的治療方法，可以幫助改善您的症狀和整體心血管健康。';
        riskLevel = 'medium';
    } else {
        status = '高風險 - 建議立即諮詢';
        description = '您可能有較明顯的心血管症狀或風險因素。強烈建議立即諮詢心血管專家進行評估。';
        recommendation = '強烈建議立即諮詢心血管專家。EECP 是一種安全、有效的非侵入性治療方法，已被廣泛用於改善心血管健康。請聯繫我們的醫療團隊進行詳細評估。';
        riskLevel = 'high';
    }
    
    resultText = status;
    
    // 顯示結果
    const resultElement = document.querySelector('.quiz-result');
    
    // 移除舊的風險等級class
    resultElement.classList.remove('risk-low', 'risk-medium', 'risk-high');
    // 添加新的風險等級class
    resultElement.classList.add('risk-' + riskLevel);
    
    document.getElementById('resultStatus').textContent = status;
    document.getElementById('resultDescription').textContent = description;
    document.getElementById('resultScore').textContent = totalScore;
    document.getElementById('resultRecommendation').textContent = recommendation;
    
    // 隱藏問題，顯示結果
    document.querySelector('.quiz-progress').style.display = 'none';
    document.querySelectorAll('.quiz-question').forEach(q => {
        q.classList.remove('active');
        q.style.display = 'none';
    });
    resultElement.classList.add('active');
}

function resetQuiz() {
    // 重置所有變數
    currentQuestionNumber = 1;
    answers = {};
    totalScore = 0;
    
    // 清除所有選項
    document.querySelectorAll('.quiz-option input[type="radio"]').forEach(radio => {
        radio.checked = false;
    });
    
    // 禁用所有下一題和查看結果按鈕
    for (let i = 1; i <= 7; i++) {
        const nextBtn = document.getElementById('nextBtn' + i);
        if (nextBtn) nextBtn.disabled = true;
    }
    const resultBtn = document.getElementById('resultBtn8');
    if (resultBtn) resultBtn.disabled = true;
    
    // 隱藏所有問題
    document.querySelectorAll('.quiz-question').forEach(q => {
        q.classList.remove('active');
        q.style.display = '';  // 重新顯示問題
    });
    
    // 重置顯示
    document.querySelector('.quiz-progress').style.display = 'block';
    document.querySelector('.quiz-result').classList.remove('active');
    document.querySelector('.quiz-form').classList.remove('active');
    document.querySelector('.quiz-question[data-question="1"]').classList.add('active');
    updateProgress();
}

function showForm() {
    document.querySelector('.quiz-result').classList.remove('active');
    document.querySelector('.quiz-form').classList.add('active');
    
    // 設置評估結果文字和樣式
    const formResultElement = document.getElementById('formResultStatus');
    const formResultDisplay = document.querySelector('.form-result-display');
    formResultElement.textContent = resultText;
    
    // 移除舊的風險等級class
    formResultElement.classList.remove('risk-low', 'risk-medium', 'risk-high');
    formResultDisplay.classList.remove('risk-low', 'risk-medium', 'risk-high');
    
    // 根據分數添加對應的風險等級class
    if (totalScore <= 8) {
        formResultElement.classList.add('risk-low');
        formResultDisplay.classList.add('risk-low');
    } else if (totalScore <= 16) {
        formResultElement.classList.add('risk-medium');
        formResultDisplay.classList.add('risk-medium');
    } else {
        formResultElement.classList.add('risk-high');
        formResultDisplay.classList.add('risk-high');
    }
    
    // 刷新驗證碼並啟動倒數計時
    refreshQuizCaptcha();
}

function backToResult() {
    document.querySelector('.quiz-form').classList.remove('active');
    document.querySelector('.quiz-result').classList.add('active');
}

function submitQuizForm(event) {
    event.preventDefault();
    
    const submitBtn = document.getElementById('quiz-submit-btn');
    const captchaError = document.getElementById('quiz-captcha-error');
    const captchaInput = document.getElementById('quizCaptcha');
    
    // 檢查驗證碼輸入框狀態
    if (captchaInput && captchaInput.readOnly) {
        alert('驗證碼已失效，請點擊刷新圖示重新取得驗證碼');
        const quizRefreshBtn = document.getElementById('quiz-refresh-captcha-btn');
        if (quizRefreshBtn) {
            quizRefreshBtn.focus();
        }
        return false;
    }
    
    // 禁用提交按鈕避免重複提交
    submitBtn.disabled = true;
    submitBtn.textContent = '送出中...';
    
    const formData = new FormData();
    formData.append('name', document.getElementById('userName').value);
    formData.append('phone', document.getElementById('userPhone').value);
    formData.append('email', document.getElementById('userEmail').value);
    formData.append('result', resultText);
    formData.append('score', totalScore);
    formData.append('quiz_captcha', document.getElementById('quizCaptcha').value);  // 使用 quiz_captcha 欄位名
    
    // 獲取 CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // 使用 fetch API 發送 AJAX 請求
    fetch('/EECP/api/submit-quiz-result/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 儲存成功訊息到 sessionStorage
            sessionStorage.setItem('quizSubmitted', 'true');
            
            // 重新整理頁面
            window.location.reload();
        } else {
            // 顯示錯誤訊息
            if (data.errors) {
                if (data.errors.quiz_captcha || data.errors.captcha) {
                    captchaError.textContent = data.errors.quiz_captcha || data.errors.captcha;
                    captchaError.style.display = 'block';
                    
                    // 刷新驗證碼
                    refreshQuizCaptcha();
                } else {
                    alert(data.message || '送出失敗，請檢查您的輸入並重試。');
                }
            } else {
                alert(data.message || '送出失敗，請稍後再試。');
            }
        }
    })
    .catch(error => {
        console.error('提交錯誤:', error);
        alert('網絡錯誤，請檢查您的網絡連接後再試。');
    })
    .finally(() => {
        // 重新啟用提交按鈕
        submitBtn.disabled = false;
        submitBtn.textContent = '送出';
    });
}

// 測驗表單驗證碼刷新功能
function refreshQuizCaptcha() {
    const refreshUrl = '/EECP/api/refresh-captcha/';
    const imageUrl = '/EECP/api/captcha-image/';
    const captchaImage = document.getElementById('quiz-captcha-image');
    const captchaInput = document.getElementById('quizCaptcha');
    
    fetch(refreshUrl)
        .then(response => response.json())
        .then(data => {
            captchaImage.src = imageUrl + "?t=" + data.timestamp;
            captchaInput.value = '';
            startQuizCaptchaCountdown();
        })
        .catch(error => {
            console.error('刷新驗證碼失敗:', error);
        });
}

// 測驗表單驗證碼倒數計時
let quizCountdownInterval;
function startQuizCaptchaCountdown() {
    clearInterval(quizCountdownInterval);
    let remaining = 30; // 30 秒
    
    const captchaTimer = document.getElementById('quiz-captcha-timer');
    const captchaInput = document.getElementById('quizCaptcha');
    const captchaImage = document.getElementById('quiz-captcha-image');
    
    // 檢查必要元素是否存在
    if (!captchaTimer || !captchaInput || !captchaImage) {
        console.warn('測驗表單驗證碼元素未找到');
        return;
    }
    
    // 重置為初始狀態
    captchaTimer.innerHTML = '驗證碼將於 <span id="quiz-countdown">0:30</span> 後失效';
    captchaTimer.className = 'form-text text-muted';  // 重置為灰色文字
    captchaTimer.style.display = 'block';
    captchaInput.disabled = false;
    captchaInput.readOnly = false;  // 確保移除 readonly
    captchaInput.placeholder = '請輸入5位數字驗證碼';
    captchaInput.style.cursor = '';
    captchaInput.style.backgroundColor = '';  // 重置背景色
    captchaImage.style.opacity = '1';
    
    console.log('測驗表單驗證碼倒數開始');
    
    quizCountdownInterval = setInterval(() => {
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        
        // 每次都重新獲取元素（防止 DOM 更新）
        const countdownEl = document.getElementById('quiz-countdown');
        if (countdownEl) {
            countdownEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
        
        if (remaining === 0) {
            clearInterval(quizCountdownInterval);
            console.log('測驗表單驗證碼已過期');
            
            // 更新計時器顯示為失效訊息
            captchaTimer.innerHTML = '驗證碼已失效，請點擊刷新圖示重新取得';
            captchaTimer.className = 'form-text text-danger';
            captchaTimer.style.display = 'block';
            
            // 使用 readonly 代替 disabled（readonly 可以顯示 placeholder）
            captchaInput.readOnly = true;
            captchaInput.disabled = false;  // 確保不是 disabled 狀態
            // captchaInput.placeholder = '驗證碼已失效，請點擊刷新圖示';
            captchaInput.value = '';
            captchaInput.style.cursor = 'not-allowed';
            captchaInput.style.backgroundColor = '#f5f5f5';
            captchaImage.style.opacity = '0.5';
            
            console.log('已設置測驗表單 placeholder:', captchaInput.placeholder);
        }
        
        remaining--;
    }, 1000);
}

// ========================================
// 預約諮詢表單驗證碼功能
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
    if (sessionStorage.getItem('quizSubmitted') === 'true') {
        sessionStorage.removeItem('quizSubmitted');
        alert('感謝您完成測驗，我們會儘快與您聯繫。');
        // 平滑滾動到測驗區域
        setTimeout(() => {
            const quizSection = document.getElementById('eecp-suitable');
            if (quizSection) {
                quizSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);
    }
    
    if (sessionStorage.getItem('contactSubmitted') === 'true') {
        const message = sessionStorage.getItem('contactMessage') || '您的訊息已成功送出，感謝您的聯繫！';
        sessionStorage.removeItem('contactSubmitted');
        sessionStorage.removeItem('contactMessage');
        alert(message);
        // 平滑滾動到聯絡表單區域
        setTimeout(() => {
            const contactSection = document.getElementById('contact-area');
            if (contactSection) {
                contactSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);
    }
    
    const refreshBtn = document.getElementById('refresh-captcha-btn');
    const captchaImage = document.getElementById('captcha-image');
    // 更完整的選擇器，確保能找到 Django 表單渲染的 input
    // 使用父容器 #contactForm 確保選到正確的表單
    let captchaInput = document.querySelector('#contactForm input[name="captcha"]') || 
                       document.querySelector('#contactForm #id_captcha') ||
                       document.querySelector('input[type="text"][placeholder*="驗證碼"]');
    const captchaTimer = document.getElementById('captcha-timer');
    
    let expiryTime = 30; // 30 秒
    let countdownInterval;

    function startCountdown() {
        clearInterval(countdownInterval);
        let remaining = expiryTime;
        
        // 重新獲取驗證碼輸入框（防止 DOM 更新後丟失引用）
        // 使用父容器 #contactForm 確保選到正確的表單
        captchaInput = document.querySelector('#contactForm input[name="captcha"]') || 
                      document.querySelector('#contactForm #id_captcha') ||
                      document.querySelector('input[type="text"][placeholder*="驗證碼"]');
        
        // 檢查元素是否存在
        if (!captchaTimer) {
            console.warn('預約表單驗證碼計時器未找到');
            return;
        }
        
        if (!captchaInput) {
            console.warn('預約表單驗證碼輸入欄位未找到，請檢查 HTML 結構');
            return;
        }
        
        console.log('預約表單驗證碼倒數開始，輸入框:', captchaInput);
        
        // 重置為初始狀態
        captchaTimer.innerHTML = '驗證碼將於 <span id="countdown">0:30</span> 後失效';
        captchaTimer.className = 'form-text text-muted';
        captchaTimer.style.display = 'block';
        captchaInput.placeholder = '請輸入5位數字驗證碼';
        captchaInput.disabled = false;
        captchaInput.readOnly = false;  // 確保移除 readonly
        captchaInput.style.cursor = '';
        captchaInput.style.backgroundColor = '';  // 重置背景色
        if (captchaImage) {
            captchaImage.style.opacity = '1';
        }
        
        countdownInterval = setInterval(() => {
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            
            // 每次都重新獲取倒數元素
            const countdownEl = document.getElementById('countdown');
            if (countdownEl) {
                countdownEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
            
            if (remaining === 0) {
                clearInterval(countdownInterval);
                console.log('預約表單驗證碼已過期');
                
                // 重新獲取輸入框（確保引用最新）
                const currentInput = document.querySelector('#contactForm input[name="captcha"]') || 
                                    document.querySelector('#contactForm #id_captcha') ||
                                    document.querySelector('input[type="text"][placeholder*="驗證碼"]');
                
                // 更新計時器顯示為失效訊息
                captchaTimer.innerHTML = '驗證碼已失效，請點擊刷新圖示重新取得';
                captchaTimer.className = 'form-text text-danger';
                captchaTimer.style.display = 'block';
                
                // 使用 readonly 代替 disabled（readonly 可以顯示 placeholder）
                if (currentInput) {
                    currentInput.readOnly = true;
                    currentInput.disabled = false;  // 確保不是 disabled 狀態
                    // currentInput.placeholder = '驗證碼已失效，請點擊刷新圖示';
                    currentInput.value = '';
                    currentInput.style.cursor = 'not-allowed';
                    currentInput.style.backgroundColor = '#f5f5f5';
                    console.log('已設置預約表單 placeholder:', currentInput.placeholder);
                } else {
                    console.warn('預約表單過期時無法找到輸入框');
                }
                
                // 調整圖片透明度
                if (captchaImage) {
                    captchaImage.style.opacity = '0.5';
                }
            }
            
            remaining--;
        }, 1000);
    }

    // 刷新驗證碼圖片
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            this.style.transform = 'rotate(360deg)';
            setTimeout(() => this.style.transform = '', 300);
            
            const refreshUrl = '/EECP/api/refresh-captcha/';
            const imageUrl = '/EECP/api/captcha-image/';
            
            console.log('開始刷新驗證碼...');
            
            fetch(refreshUrl)
                .then(response => {
                    console.log('Response status:', response.status);
                    if (!response.ok) {
                        throw new Error('HTTP error! status: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('收到數據:', data);
                    if (captchaImage) {
                        captchaImage.src = imageUrl + "?t=" + data.timestamp;
                    }
                    
                    // 重新獲取驗證碼輸入框
                    if (!captchaInput) {
                        captchaInput = document.querySelector('input[name="captcha"]') || 
                                      document.querySelector('#id_captcha') ||
                                      document.querySelector('input[type="text"][placeholder*="驗證碼"]');
                    }
                    
                    if (captchaInput) {
                        captchaInput.value = '';
                    }
                    startCountdown();
                })
                .catch(error => {
                    console.error('刷新驗證碼失敗:', error);
                    alert('無法刷新驗證碼：' + error.message);
                });
        });
    }

    startCountdown();
    
    // 預約諮詢表單 AJAX 提交
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('contact-submit-btn');
            const captchaError = document.getElementById('contact-captcha-error');
            
            // 檢查驗證碼輸入框狀態
            const captchaInput = document.querySelector('#contactForm input[name="captcha"]') || 
                                document.querySelector('#contactForm #id_captcha');
            
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
            submitBtn.innerHTML = '<span>送出中...</span>';
            
            const formData = new FormData(contactForm);
            
            // 取得 CSRF Token
            const csrftoken = getCookie('csrftoken');

            // 使用 fetch API 發送 AJAX 請求
            fetch(contactForm.action || window.location.href, {
                method: 'POST',
                credentials: 'include',  // 關鍵：強制傳輸Cookie
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')  // 手動加入CSRF
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
    
    // 初始化 EECP 測驗功能
    if (document.querySelector('.eecp-test')) {
        initQuiz();
        
        // 測驗表單提交
        const quizContactForm = document.getElementById('quizContactForm');
        if (quizContactForm) {
            quizContactForm.addEventListener('submit', submitQuizForm);
        }
        
        // 測驗表單驗證碼刷新按鈕
        const quizRefreshBtn = document.getElementById('quiz-refresh-captcha-btn');
        if (quizRefreshBtn) {
            quizRefreshBtn.addEventListener('click', function() {
                this.style.transform = 'rotate(360deg)';
                setTimeout(() => this.style.transform = '', 300);
                refreshQuizCaptcha();
            });
        }
    }
    
    // 啟動預約表單驗證碼倒數計時
    startCountdown();
    
    // EECP 影片點擊播放
    const eecpVideoPlayer = document.querySelector('.youtube-player[data-id="QdQPjEKfsoI"]');
    if (eecpVideoPlayer) {
        eecpVideoPlayer.addEventListener('click', function() {
            const videoId = this.dataset.id;
            if (videoId) {
                const iframe = document.createElement('iframe');
                iframe.setAttribute('src', 'https://www.youtube.com/embed/' + videoId + '?rel=0&autoplay=1');
                iframe.setAttribute('frameborder', '0');
                iframe.setAttribute('allowfullscreen', '1');
                iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share');
                iframe.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
                iframe.setAttribute('loading', 'lazy');
                iframe.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 100;';
                
                // 移除圖片和播放按鈕，替換為 iframe
                this.innerHTML = '';
                this.appendChild(iframe);
            }
        });
    }
});