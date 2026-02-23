// 取得按鈕
const mybutton = document.getElementById('myBtn');

// 全域函式供 inline onclick="topFunction()" 使用，產生平滑動畫效果
function topFunction() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 判斷是否為大螢幕 (>= 992px)
function isLargeScreen() {
    return window.matchMedia('(min-width: 992px)').matches;
}

// 當使用者滾動時，顯示或隱藏按鈕（僅大螢幕）
if (mybutton) {
    function updateMyButtonVisibility() {
        if (!isLargeScreen()) {
            mybutton.style.display = 'none';
            return;
        }
        if (window.scrollY > 20) {
            mybutton.style.display = 'block';
        } else {
            mybutton.style.display = 'none';
        }
    }

    window.addEventListener('scroll', updateMyButtonVisibility);
    window.addEventListener('resize', updateMyButtonVisibility);

    // 初始檢查
    updateMyButtonVisibility();

    // 點擊按鈕時，平滑滾動到最上方
    mybutton.addEventListener('click', () => {
        // 保留或替代 topFunction 的行為
        topFunction();
    });
}