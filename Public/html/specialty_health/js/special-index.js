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

    fetch('/specialty_health/api/banner-data/')
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

// 最新消息
document.addEventListener("DOMContentLoaded", function () {
    fetch("/specialty_health/api/health-news-home/")
        .then(res => res.json())
        .then(data => {
            const newsSection = document.querySelector("#news .news-box");
            if (!newsSection) return;

            const titleDiv = document.createElement("div");
            titleDiv.classList.add("a_tit_1", "mt-5");
            titleDiv.innerHTML = `<h2 class="mb-0">最新消息<span><br class="d-block d-lg-none"> Health News</span></h2>`;
            newsSection.appendChild(titleDiv);

            const ul = document.createElement("ul");
            ul.classList.add("list-unstyled");

            data.news.forEach(item => {
                const li = document.createElement("li");
                li.classList.add("news-item");
                li.innerHTML = `
                    <span class="news-date">${item.date}</span>
                    <a href="${item.url}" class="font-weight-bold">${item.title}</a>
                `;
                ul.appendChild(li);
            });

            newsSection.appendChild(ul);
        });
});

// 影音專區
document.addEventListener("DOMContentLoaded", function () {
    fetch('/specialty_health/api/health-film-home/')
        .then(res => res.json())
        .then(res => {
            const videoList = document.getElementById('video-list-home');
            videoList.innerHTML = '';
            res.videos.forEach(v => {
                const div = document.createElement('div');
                div.className = 'col-lg-4 mb-4';
                div.innerHTML = `
                    <figure class="card video-card h-100 shadow-sm article-card fade-in-card" data-url="${v.youtube_url}" data-title="${v.title}">
                        <img src="${v.youtube_image}" class="card-img-top" alt="${v.title}">
                        <figcaption class="card-body">
                            <small class="card-text text-muted">上架時間：${v.date}</small>
                            <h5 class="card-title">${v.title}</h5>
                        </figcaption>
                    </figure>
                `;
                videoList.appendChild(div);
            });
        });

    // 動態創建並顯示 Modal
    document.getElementById('video-list-home').addEventListener('click', function (e) {
        let target = e.target;
        while (target && !target.classList.contains('video-card')) {
            target = target.parentElement;
        }
        if (target && target.classList.contains('video-card')) {
            const url = target.getAttribute('data-url');
            const title = target.querySelector('.card-title').textContent;
            if (typeof openVideoModal === 'function') {
                openVideoModal(url, title);
            }
        }
    });
});

// 媒體報導
document.addEventListener("DOMContentLoaded", function () {
    fetch("/specialty_health/api/health-media-home/")
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('media-articles-home');
            container.innerHTML = '';
            if (!data.articles || data.articles.length === 0) {
                container.innerHTML = `
                    <div class="col-12 text-center my-4">
                        <p class="text-muted">目前暫無文章</p>
                    </div>
                `;
                return;
            }
            data.articles.forEach(article => {
                container.innerHTML += `
                    <div class="col-md-4 mb-4">
                        <a href="${article.url}">
                            <figure class="card h-100 shadow-sm fade-in-card article-card">
                                <div class="img-container">
                                    <img src="/media/${article.image}" class="card-img-top" alt="${article.title}" loading="lazy">
                                </div>
                                <figcaption class="card-body d-flex flex-column">
                                    <h5 class="card-title">${article.title}</h5>
                                    <p class="card-text">${article.summary}</p>
                                    <small class="text-muted mt-auto ml-auto">發表日期：${article.pub_date}</small>
                                </figcaption>
                            </figure>
                        </a>
                    </div>
                `;
            });
        });
});

// Google Map 延遲載入
document.addEventListener("DOMContentLoaded", () => {
    const mapSection = document.querySelector("#map .map-container");
    if (!mapSection) return;
    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && mapSection.dataset.mapLoaded === "false") {
                const iframe = document.createElement('iframe');
                iframe.src = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3641.1555465604415!2d120.71709177534782!3d24.13117497841248!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x346922c9a6996b67%3A0xa9f0b272143823e6!2z6ZW35a6J6Yar6Zmi!5e0!3m2!1szh-TW!2stw!4v1754482945439!5m2!1szh-TW!2stw";
                iframe.allowFullscreen = "";
                iframe.loading = "lazy";
                mapSection.innerHTML = "";
                mapSection.appendChild(iframe);
                mapSection.dataset.mapLoaded = "true";
                obs.unobserve(mapSection);
            }
        });
    }, { threshold: 0.1 });
    observer.observe(mapSection);
});