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
            !link.hasAttribute('data-no-loading')) {
            showLoading();
        }
    });

    // ✅ 修改：監聽瀏覽器的上一頁/下一頁按鈕
    window.addEventListener('popstate', function() {
        showLoading();
        // 使用 requestAnimationFrame 確保 loading 有顯示後再隱藏
        requestAnimationFrame(function() {
            setTimeout(hideLoading, MIN_LOADING_TIME);
        });
    });

    // ✅ 新增：監聽 beforeunload（頁面即將卸載時顯示 loading）
    window.addEventListener('beforeunload', function() {
        showLoading();
    });
})();