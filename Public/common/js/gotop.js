// 取得按鈕
const mybutton = document.getElementById('myBtn');

// 當使用者滾動時，顯示或隱藏按鈕
window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
        mybutton.style.display = 'block';
    } else {
        mybutton.style.display = 'none';
    }
});

// 點擊按鈕時，平滑滾動到最上方
mybutton.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});


// 自動設定今年年份
document.addEventListener('DOMContentLoaded', function() {
    const yearSpan = document.getElementById('currentYear');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }
});