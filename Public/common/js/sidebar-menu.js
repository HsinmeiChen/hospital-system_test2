/**
 * 全站側邊選單通用收合腳本 (sidebar-menu.js)
 * 只要父層有 .js-sidebar-wrapper，點擊 .js-sidebar-toggle 就會切換 .is-open
 */
document.addEventListener('DOMContentLoaded', function() {
    // 1. 點擊開關
    document.addEventListener('click', function(e) {
        // 尋找最近的切換按鈕
        const toggle = e.target.closest('.js-sidebar-toggle');
        if (!toggle) return;

        // 尋找對應的選單容器
        const sidebar = toggle.closest('.js-sidebar-wrapper');
        if (sidebar && window.innerWidth < 992) {
            sidebar.classList.toggle('is-open');
        }
    });

    // 2. RWD 視窗縮放重置 (當回到桌機版時自動關閉開啟狀態)
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) {
            document.querySelectorAll('.js-sidebar-wrapper.is-open').forEach(el => {
                el.classList.remove('is-open');
            });
        }
    });
});
