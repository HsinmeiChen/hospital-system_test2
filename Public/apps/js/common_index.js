// Banner 輪播效果
document.addEventListener("DOMContentLoaded", () => {
    const carousel = document.getElementById('banner-carousel');
    const dotsContainer = document.getElementById('banner-dots');
    const prevBtn = document.getElementById('prevBanner');
    const nextBtn = document.getElementById('nextBanner');
    const bannerSection = document.getElementById('banner');
    let slides = [];
    let dots = [];
    let current = 0;
    let timer = null;

    // 自動輪播
    function startAutoPlay() {
        timer = setInterval(() => switchSlide(current + 1), 6000);
    }
    function stopAutoPlay() {
        clearInterval(timer);
    }
    function switchSlide(index) {
        slides[current].classList.remove('active');
        dots[current].classList.remove('active');
        current = (index + slides.length) % slides.length;
        slides[current].classList.add('active');
        dots[current].classList.add('active');
    }

    fetch(API_URL_BANNER)
        .then(res => res.json())
        .then(data => {
            data.banners.forEach((item, index) => {
                const slide = document.createElement('figure');
                slide.classList.add('banner-slide');
                if (index === 0) {
                    setTimeout(() => {
                        slide.classList.add('active');
                        dots[0].classList.add('active');
                    }, 50);
                }
                const linkStart = item.link ? `<a href="${item.link}" class="banner-link" data-link="${item.link}">` : '';
                const linkEnd = item.link ? `</a>` : '';
                slide.innerHTML = `
                    ${linkStart}
                    <picture>
                        <source type="image/webp" media="(max-width: 768px)" srcset="/media/${item.mb_webp}">
                        <source media="(max-width: 768px)" srcset="/media/${item.mb}">
                        <source type="image/webp" srcset="/media/${item.pc_webp}">
                        <img src="/media/${item.pc}" class="w-100" loading="lazy" alt="Banner ${item.key}">
                    </picture>
                    ${linkEnd}
                `;
                carousel.appendChild(slide);
                slides.push(slide);

                // 新增：如果有 link，掛事件（支援 YouTube 彈窗）
                if (item.link) {
                    slide.addEventListener('click', function (e) {
                        let target = e.target;
                        while (target && target !== slide && !(target.classList && target.classList.contains('banner-link'))) {
                            target = target.parentElement;
                        }
                        if (target && target.classList && target.classList.contains('banner-link')) {
                            const link = target.getAttribute('data-link');
                            if (/youtube\.com|youtu\.be/.test(link)) {
                                e.preventDefault();
                                const title = item.title || `影片`;
                                if (typeof openVideoModal === 'function') {
                                    openVideoModal(link, title);
                                }
                            }
                            // 不是 YouTube 則預設跳轉
                        }
                    });
                }

                // 導覽圓點
                const dot = document.createElement('div');
                dot.classList.add('dot');
                if (index === 0) dot.classList.add('active');
                dot.addEventListener('click', () => {
                    stopAutoPlay();
                    switchSlide(index);
                    startAutoPlay();
                });
                dotsContainer.appendChild(dot);
                dots.push(dot);
            });
            startAutoPlay();
        });

    prevBtn.addEventListener('click', () => {
        stopAutoPlay();
        switchSlide(current - 1);
        startAutoPlay();
    });
    nextBtn.addEventListener('click', () => {
        stopAutoPlay();
        switchSlide(current + 1);
        startAutoPlay();
    });

    // 滑鼠懸停 → 暫停輪播 + 放大
    carousel.addEventListener('mouseenter', () => {
        stopAutoPlay();
        const img = slides[current].querySelector('img');
        const computedStyle = window.getComputedStyle(img);
        const matrix = new WebKitCSSMatrix(computedStyle.transform);
        const scale = matrix.a;
        img.style.transform = `scale(${scale})`;
        img.style.transition = 'none';
    });
    carousel.addEventListener('mouseleave', () => {
        const img = slides[current].querySelector('img');
        requestAnimationFrame(() => {
            img.style.transition = 'transform 3s linear';
            img.style.transform = 'scale(1.05)';
        });
        startAutoPlay();
    });

    // 觸控滑動支援
    let startX = 0;
    let isSwiping = false;
    bannerSection.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        isSwiping = true;
    }, { passive: true });
    bannerSection.addEventListener('touchmove', (e) => {
        if (!isSwiping) return;
        const deltaX = e.touches[0].clientX - startX;
        if (Math.abs(deltaX) > 50) {
            stopAutoPlay();
            if (deltaX > 0) {
                switchSlide(current - 1);
            } else {
                switchSlide(current + 1);
            }
            isSwiping = false;
            startAutoPlay();
        }
    }, { passive: true });
    bannerSection.addEventListener('touchend', () => {
        isSwiping = false;
    });
});

// 影音專區
document.addEventListener("DOMContentLoaded", function () {
    fetch(API_URL_FILM_HOME)
        .then(res => res.json())
        .then(res => {
            const videoList = document.getElementById('video-list-home');
            videoList.innerHTML = '';
            res.videos.forEach(v => {
                const div = document.createElement('div');
                div.innerHTML = `
                    <a href="${v.youtube_url}" class="video-card-link" target="_blank" title="播放衛教影片：${(v.title || '').replace(/"/g, '&quot;')}" aria-label="播放衛教影片：${(v.title || '').replace(/"/g, '&quot;')}">
                        <figure class="video-card fade-in-card" data-url="${v.youtube_url}" data-title="${v.title}">
                            <div class="video-thumb">
                                <img src="${v.youtube_image}" class="card-img-top" alt="${(v.title || '').replace(/"/g, '&quot;')}" onload="if(this.naturalWidth <= 120) { this.onload=null; this.src='https://img.youtube.com/vi/${v.youtube_id}/hqdefault.jpg'; }" onerror="this.onerror=null; this.src='https://img.youtube.com/vi/${v.youtube_id}/hqdefault.jpg';">
                                <div class="play-btn-small-overlay">
                                    <span class="material-symbols-outlined" style="font-size: 60px; color: rgba(255,255,255,0.9);">play_circle</span>
                                </div>
                            </div>
                            <figcaption class="video-card-content video-seo-only">
                                <h5 class="video-card-title">${v.title}</h5>
                                <p class="video-card-meta">上架時間：${v.date}</p>
                            </figcaption>
                        </figure>
                    </a>
                `;
                videoList.appendChild(div);
            });
        });

    // 動態創建並顯示 Modal
    document.getElementById('video-list-home').addEventListener('click', function (e) {
        let target = e.target;
        while (target && target !== this && !target.classList.contains('video-card')) {
            target = target.parentElement;
        }
        if (target && target.classList.contains('video-card')) {
            e.preventDefault(); // 阻止外層 <a> 連結的網頁跳轉，改用 Modal 播放
            const url = target.getAttribute('data-url');
            const title = target.getAttribute('data-title') || '';
            if (typeof openVideoModal === 'function') {
                openVideoModal(url, title);
            }
        }
    });
});