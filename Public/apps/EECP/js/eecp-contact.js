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
    
    if (captchaError) {
        captchaError.textContent = '';
        captchaError.style.display = 'none';
    }
    
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
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
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
    const refreshUrl = '/api/captcha/refresh/';
    const captchaImage = document.getElementById('quiz-captcha-image');
    const captchaInput = document.getElementById('quizCaptcha');
    
    // 隱藏錯誤提示訊息
    const captchaError = document.getElementById('quiz-captcha-error');
    if (captchaError) {
        captchaError.textContent = '';
        captchaError.style.display = 'none';
    }
    
    fetch(refreshUrl)
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
            // 使用後端回傳的 captcha_url 確保圖片真正更新
            if (captchaImage) {
                captchaImage.src = data.captcha_url || ('/api/captcha/image/?t=' + data.timestamp);
            }
            if (captchaInput) {
                captchaInput.value = '';
            }
            startQuizCaptchaCountdown();
        })
        .catch(error => {
            console.error('刷新驗證碼失敗:', error);
        });
}

// 測驗表單驗證碼初始化狀態（已取消倒數計時）
function startQuizCaptchaCountdown() {
    const captchaTimer = document.getElementById('quiz-captcha-timer');
    const captchaInput = document.getElementById('quizCaptcha');
    const captchaImage = document.getElementById('quiz-captcha-image');
    
    // 隱藏倒數計時提示元件
    if (captchaTimer) {
        captchaTimer.style.display = 'none';
    }
    
    if (captchaInput) {
        captchaInput.disabled = false;
        captchaInput.readOnly = false;
        captchaInput.placeholder = '請輸入5位數字驗證碼';
        captchaInput.style.cursor = '';
        captchaInput.style.backgroundColor = '';
    }
    
    if (captchaImage) {
        captchaImage.style.opacity = '1';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // 檢查是否有測驗表單提交成功的標記
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