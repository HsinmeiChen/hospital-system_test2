const weekbtn = document.getElementById('weekbtn');
const footer = document.getElementById('footer');

// 當使用者滾動時，顯示或隱藏按鈕 (網掛預約-上下週切換按鈕)
let isFooterVisible = false;

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        isFooterVisible = entry.isIntersecting;
        updateButton();
    });
});

observer.observe(footer);

window.addEventListener('scroll', updateButton);

function updateButton() {
    if (window.scrollY > 700 && !isFooterVisible) {
        weekbtn.style.display = 'flex';
    } else {
        weekbtn.style.display = 'none';
    }
}