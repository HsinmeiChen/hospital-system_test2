// ■■■■■■■■■■■■■■■■■■■■■■■■■■ 側邊隨機 5 筆文章-媒體報導 ■■■■■■■■■■■■■■■■■■■■■■■■■■
function loadRandomHealthReports() {
    const container = document.getElementById('random-reports');
    // 如果畫面上根本沒有這個區塊，就直接結束，不要浪費網路資源去抓 API
    if (!container) return;
    // 動態載入雜誌風格的 CSS
    if (!document.getElementById('magazine-style-css')) {
        const style = document.createElement('style');
        style.id = 'magazine-style-css';
        style.innerHTML = `
            .magazine-card { transition: all 0.3s ease; }
            .magazine-card:hover .magazine-img { transform: scale(1.05); }
            .magazine-card:hover .magazine-title { color: var(--primary) !important; }
            .magazine-card .img-container { overflow: hidden; border-radius: 4px; }
        `;
        document.head.appendChild(style);
    }

    fetch(API_URL_RANDOM_REPORTS)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('random-reports');
            if (!container) return;
            container.innerHTML = '';
            data.articles.forEach(article => {

                // 先建立外層 div
                const wrapper = document.createElement('div');
                wrapper.className = 'col-6 col-lg-12';

                // 建立 figure                
                const card = document.createElement('figure');
                card.className = 'fade-in-card magazine-card';
                card.style.cursor = 'pointer';
                card.style.border = 'none';
                card.style.backgroundColor = 'transparent';
                card.innerHTML = `
                    <div class="row g-3 align-items-center no-gutters">  
                        <div class="col-4">
                            <figure class="img-container h-100 position-relative m-0">
                                <picture>
                                    <source srcset="/media/${article.image}" type="image/webp">
                                    <img src="/media/${article.image.replace('/thumb_webp/', '/').replace('/img_webp_article/', '/').replace('/img_webp_news/', '/').replace(/\.webp$/i, '.jpg')}" class="img-fluid w-100 h-100 magazine-img" style="aspect-ratio: 4/3; object-fit: cover; transition: transform 0.5s ease;" alt="${article.filename_title}" title="${article.filename_title}" loading="lazy" decoding="async">
                                </picture>
                                <figcaption class="d-none">${article.filename_title}</figcaption>
                            </figure>
                        </div>                      
                        <div class="col-8">
                            <figcaption class="d-flex flex-column justify-content-center h-100 pl-2">
                                <div class="mb-2" style="font-size: 0.75rem; letter-spacing: 1.5px; color: var(--outline); text-transform: uppercase;">
                                    <span style="color: var(--color-accent-peach, #d9534f); font-weight: bold;">NEWS</span> <span style="margin: 0 4px;">|</span> ${article.pub_date}
                                </div>
                                <h5 class="magazine-title mb-2" style="font-size:1rem; font-weight:700; line-height: 1.5; height: 3rem; color: var(--on-surface); transition: color 0.3s; text-align:justify; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${article.filename_title}</h5>
                            </figcaption>
                        </div>
                        
                    </div>
                `;

                // 點擊直接跳轉頁面（刷新並更新網址）
                card.onclick = function() {
                    window.location.href = URL_ARTICLE_DETAIL.replace('PLACEHOLDER', article.filename);
                };

                // 把 figure 放進外層 div
                wrapper.appendChild(card);

                // 再把外層 div 丟進 container
                container.appendChild(wrapper);
            });
        });
}

document.addEventListener('DOMContentLoaded', loadRandomHealthReports);


// ■■■■■■■■■■■■■■■■■■■■■■■■■■ 側邊隨機 5 筆-衛教園地 ■■■■■■■■■■■■■■■■■■■■■■■■■■
function loadRandomHealthEdus() {
    // 動態載入排名列表的 CSS
    if (!document.getElementById('ranked-list-style-css')) {
        const style = document.createElement('style');
        style.id = 'ranked-list-style-css';
        style.innerHTML = `
            .ranked-article-card { 
                transition: background-color 0.3s ease; 
                padding: 12px 8px;
                border-bottom: 1px dashed var(--outline-variant);
                background-color: transparent;
            }
            .ranked-article-card:last-child {
                border-bottom: none;
            }
            .ranked-article-card:hover { 
                background-color: var(--surface-container-low);
            }
            .ranked-article-card:hover .ranked-title { color: var(--primary) !important; }
            .rank-number { 
                font-size: 1rem; 
                font-weight: 600; 
                color: var(--outline); 
                min-width: 26px;
                height: 26px;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: var(--surface-container-low);
                border-radius: 4px;
                margin-right: 12px;
                font-family: inherit;
                transition: background-color 0.3s, color 0.3s;
                line-height: 1;
            }
            .ranked-article-card:hover .rank-number { 
                background-color: var(--primary); 
                color: var(--on-white);
            }
            .ranked-title {
                font-size: 0.95rem;
                font-weight: 500;
                color: var(--on-surface-variant);
                margin: 0;
                line-height: 1.4;
                transition: color 0.3s;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
        `;
        document.head.appendChild(style);
    }

    fetch(API_URL_RANDOM_EDUS)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('random-edus');
            if (!container) return;
            container.innerHTML = '';
            
            // 加入 mb-4 (或 mb-5) 增加與下方區塊的距離
            const listWrapper = document.createElement('div');
            listWrapper.className = 'col-12 px-2 mb-5';
            
            data.edus.forEach((edu, index) => {
                const rank = index + 1;

                // 建立卡片             
                const card = document.createElement('div');
                card.className = 'd-flex align-items-center fade-in-card ranked-article-card';
                card.style.cursor = 'pointer';
                card.innerHTML = `
                    <div class="rank-number">${rank}</div>
                    <div class="flex-grow-1">
                        <h5 class="ranked-title">${edu.filename_title}</h5>
                    </div>
                `;

                // 點擊直接跳轉頁面
                card.onclick = function() {
                    window.location.href = URL_EDU_DETAIL.replace('PLACEHOLDER', edu.title_id);
                };

                // 把卡片放進列表外層
                listWrapper.appendChild(card);
            });
            
            container.appendChild(listWrapper);
        });
}

document.addEventListener('DOMContentLoaded', loadRandomHealthEdus);