/**
 * 主要用途是管理網站的全域載入動畫（Loading Screen），確保使用者在頁面切換、載入或使用瀏覽器導航（上一頁/下一頁）時，能有平滑且一致的視覺體驗。
 */

(function() {
    'use strict';

    // 記錄頁面開始載入時間
    window.pageLoadStart = new Date().getTime();

    // 最小顯示時間（毫秒）- 避免載入太快閃爍
    const MIN_LOADING_TIME = 300;

    // DOM 載入完成後隱藏 loading
    function hideLoading() {
        const loadingElement = document.getElementById('page-loading');
        if (!loadingElement) return;

        const loadTime = new Date().getTime() - window.pageLoadStart;
        const remainingTime = Math.max(0, MIN_LOADING_TIME - loadTime);

        setTimeout(function() {
            loadingElement.classList.add('fade-out');
            setTimeout(function() {
                loadingElement.style.display = 'none';
            }, 800); // 這裡同步 CSS 的 transition 時間 (0.8s)
        }, remainingTime);
    }

    // 顯示 loading
    function showLoading() {
        const loadingElement = document.getElementById('page-loading');
        if (loadingElement) {
            loadingElement.style.display = 'flex';
            loadingElement.classList.remove('fade-out');
            window.pageLoadStart = new Date().getTime(); // 重置計時
        }
    }

    // 監聽 DOM 載入完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', hideLoading);
    } else {
        hideLoading();
    }

    // 監聽所有圖片載入完成
    window.addEventListener('load', function() {
        setTimeout(hideLoading, 100);
    });

    // ✅ 修改：監聽 pageshow 事件（處理「上一頁」/「下一頁」）
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            // 從快取載入時，先顯示 loading 再隱藏
            showLoading();
            setTimeout(hideLoading, MIN_LOADING_TIME);
        }
    });

    // 頁面切換時顯示 loading
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (link && link.href && !link.target && 
            link.href.indexOf(window.location.host) !== -1 &&
            !link.href.includes('#') &&
            !link.href.toLowerCase().endsWith('.pdf') &&
            !link.hasAttribute('data-no-loading')) {
            showLoading();
        }
    });

    // ✅ 修改：監聽瀏覽器的上一頁/下一頁按鈕
    window.addEventListener('popstate', function() {
        // 修正 Chrome PDF 檢視器的雙重歷史紀錄問題 (避免回上一頁時卡在 PDF 初始狀態)
        // 當使用者按「上一頁」結果還是在 PDF 路徑時，自動補一次回退動作
        if (window.location.pathname.toLowerCase().endsWith('.pdf')) {
            history.back();
            return;
        }
        showLoading();
        // 使用 requestAnimationFrame 確保 loading 有顯示後再隱藏
        requestAnimationFrame(function() {
            setTimeout(hideLoading, MIN_LOADING_TIME);
        });
    });
})();