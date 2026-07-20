function loadMediaArticles(page = 1) {
    // 使用 HTML 傳過來的 API_URL_MEDIA 變數
    fetch(`${API_URL_MEDIA}?page=${page}`)
        // .then(res => res.json())
        .then(res => {
            if (!res.ok) throw new Error("API 錯誤：" + res.status);
            return res.json();
        })
        .then(data => {
            const container = document.getElementById('media-articles-container');
            container.innerHTML = '';

            // （data.articles 為空時）
            if (!data.articles || data.articles.length === 0) {
                container.innerHTML = `
                    <div class="col-12 text-center my-5">
                        <p class="text-muted mb-0 h3">暫無媒體報導</p>
                    </div>
                `;
                document.getElementById("pagination-list").innerHTML = "";
                updateItemListSchema([]); // 清空可能存在的舊 Schema
                return;
            }

            // 更新 ItemList 結構化資料
            updateItemListSchema(data.articles);

            if (data.articles && data.articles.length > 0) {
                let html = '<div class="newspaper-grid">';
                
                data.articles.forEach((article, index) => {
                    const pubDate = article.pub_date || '';
                    const title = article.title || '';
                    const summary = article.summary || '';
                    const webpImg = `/media/${article.image}`;
                    const img = webpImg.replace('/thumb_webp/', '/').replace('/img_webp_article/', '/').replace('/img_webp_news/', '/').replace(/\.webp$/i, '.jpg');
                    const url = article.url || '#';

                    // 採用 10 篇一循環的報紙排版
                    const patternIndex = index % 10;

                    if (patternIndex === 0 || patternIndex === 6) {
                        // 1. 頭條大版面 (The Lead Story) - Span 2x2
                        html += `
                            <a href="${url}" class="np-card np-hero">
                                <figure class="m-0">
                                    <picture>
                                        <source srcset="${webpImg}" type="image/webp">
                                        <img class="img-fluid w-100" src="${img}" alt="${title}" title="${title}" loading="lazy" decoding="async">
                                    </picture>
                                    <figcaption class="d-none">${title}</figcaption>
                                </figure>
                                <div class="np-content">
                                    <div class="np-meta">頭條報導</div>
                                    <h2 class="np-title">${title}</h2>
                                    <p class="np-desc">${summary}</p>
                                    <div class="np-date">${pubDate}</div>
                                </div>
                            </a>
                        `;
                    } else if (patternIndex === 1) {
                        // 2. 側邊直欄專題 (Sidebar Feature) - Span 1x2
                        html += `
                            <a href="${url}" class="np-card np-sidebar">
                                <figure class="m-0">
                                    <picture>
                                        <source srcset="${webpImg}" type="image/webp">
                                        <img class="img-fluid w-100" src="${img}" alt="${title}" title="${title}" loading="lazy" decoding="async">
                                    </picture>
                                    <figcaption class="d-none">${title}</figcaption>
                                </figure>
                                <div class="np-content">
                                    <div class="np-meta">深度專欄</div>
                                    <h3 class="np-title">${title}</h3>
                                    <p class="np-desc">${summary}</p>
                                    <div class="np-date">${pubDate}</div>
                                </div>
                            </a>
                        `;
                    } else if (patternIndex === 2) {
                        // 3. 焦點快訊 (Text-Only Brief) - Span 1x1
                        html += `
                            <a href="${url}" class="np-card np-brief">
                                <div class="np-meta" style="color: var(--on-surface-variant);">最新快訊</div>
                                <h3 class="np-title">${title}</h3>
                                <p class="np-desc">${summary}</p>
                                <div class="np-date">${pubDate}</div>
                            </a>
                        `;
                    } else if (patternIndex === 3) {
                        // 4. 圖片短訊 (Sub-feature) - Span 1x1
                        html += `
                            <a href="${url}" class="np-card np-sub">
                                <figure class="m-0">
                                    <picture>
                                        <source srcset="${webpImg}" type="image/webp">
                                        <img class="img-fluid w-100" src="${img}" alt="${title}" title="${title}" loading="lazy" decoding="async">
                                    </picture>
                                    <figcaption class="d-none">${title}</figcaption>
                                </figure>
                                <div class="np-content">
                                    <h4 class="np-title">${title}</h4>
                                    <div class="np-date">${pubDate}</div>
                                </div>
                            </a>
                        `;
                    } else if (patternIndex === 4) {
                        // 5. 橫幅分隔報導 (Horizontal Banner) - Span 3x1
                        html += `
                            <a href="${url}" class="np-card np-banner">
                                <figure class="m-0">
                                    <picture>
                                        <source srcset="${webpImg}" type="image/webp">
                                        <img class="img-fluid w-100" src="${img}" alt="${title}" title="${title}" loading="lazy" decoding="async">
                                    </picture>
                                    <figcaption class="d-none">${title}</figcaption>
                                </figure>
                                <div class="np-content">
                                    <div class="np-meta">特別企劃</div>
                                    <h3 class="np-title">${title}</h3>
                                    <p class="np-desc" style="-webkit-line-clamp: 2;">${summary}</p>
                                    <div class="np-date">${pubDate}</div>
                                </div>
                            </a>
                        `;
                    } else if (patternIndex === 7) {
                        // 6. 暗黑快訊 (Dark Brief) - Span 1x1
                        html += `
                            <a href="${url}" class="np-card np-brief-dark">
                                <div class="np-meta" style="color: var(--on-primary);">編輯精選</div>
                                <h3 class="np-title">${title}</h3>
                                <p class="np-desc">${summary}</p>
                                <div class="np-date" style="color: var(--surface-container);">${pubDate}</div>
                            </a>
                        `;
                    } else if (patternIndex === 9) {
                        // 7. 半橫幅報導 (Half Banner) - Span 2x1
                        html += `
                            <a href="${url}" class="np-card np-banner-half">
                                <figure class="m-0">
                                    <picture>
                                        <source srcset="${webpImg}" type="image/webp">
                                        <img class="img-fluid w-100" src="${img}" alt="${title}" title="${title}" loading="lazy" decoding="async">
                                    </picture>
                                    <figcaption class="d-none">${title}</figcaption>
                                </figure>
                                <div class="np-content">
                                    <div class="np-meta">觀點</div>
                                    <h3 class="np-title">${title}</h3>
                                    <div class="np-date">${pubDate}</div>
                                </div>
                            </a>
                        `;
                    } else {
                        // 8. 標準卡 (Standard Columns) - patternIndex 5, 8 - Span 1x1
                        html += `
                            <a href="${url}" class="np-card np-standard">
                                <figure class="m-0">
                                    <picture>
                                        <source srcset="${webpImg}" type="image/webp">
                                        <img class="img-fluid w-100" src="${img}" alt="${title}" title="${title}" loading="lazy" decoding="async">
                                    </picture>
                                    <figcaption class="d-none">${title}</figcaption>
                                </figure>
                                <div class="np-content">
                                    <div class="np-meta" style="color: var(--secondary);">媒體報導</div>
                                    <h4 class="np-title">${title}</h4>
                                    <div class="np-date">${pubDate}</div>
                                </div>
                            </a>
                        `;
                    }
                });
                
                html += '</div>';
                container.innerHTML = html;
            }

            const pagination = document.getElementById('pagination-list');
            pagination.innerHTML = '';
            const total = data.total_pages;
            const current = data.current_page;

            if (total > 1) {
                // 第一頁
                pagination.innerHTML += `
                    <li class="page-item ${current === 1 ? 'disabled' : ''}">
                        <a class="page-link" href="#" data-page="1">&laquo;</a>
                    </li>
                `;

                // 上一頁
                pagination.innerHTML += `
                    <li class="page-item ${current === 1 ? 'disabled' : ''}">
                        <a class="page-link" href="#" data-page="${current - 1}">&lsaquo;</a>
                    </li>
                `;

                // 下拉選單
                let selectHtml = `
                    <li class="page-item">
                        <select id="report-page-select" class="form-control form-control-sm h-100" style="width:auto; display:inline-block;">
                `;
                for (let i = 1; i <= total; i++) {
                    selectHtml += `<option value="${i}" ${i === current ? 'selected' : ''}>第 ${i} 頁</option>`;
                }
                selectHtml += `</select></li>`;
                pagination.innerHTML += selectHtml;

                // 下一頁
                pagination.innerHTML += `
                    <li class="page-item ${current === total ? 'disabled' : ''}">
                        <a class="page-link" href="#" data-page="${current + 1}">&rsaquo;</a>
                    </li>
                `;

                // 最後頁
                pagination.innerHTML += `
                    <li class="page-item ${current === total ? 'disabled' : ''}">
                        <a class="page-link" href="#" data-page="${total}">&raquo;</a>
                    </li>
                `;
                // 綁定下拉事件
                document.getElementById("report-page-select").addEventListener("change", function() {
                    loadMediaArticles(this.value);
                });
            }
        })
        
        // （API 出錯時）
        .catch(err => {
            console.error("[health-reports] API 載入失敗：", err);
            const container = document.getElementById("media-articles-container");
            container.innerHTML = `
                <div class="col-12 text-center my-5">
                    <p class="text-danger mb-0 h3">資料載入失敗，請稍後再試。</p>
                </div>
            `;
            document.getElementById("pagination-list").innerHTML = "";
        });
}

// 點擊分頁
$(document).on("click", "#pagination-list .page-link", function(e) {
    e.preventDefault();
    if ($(this).parent().hasClass("disabled")) return; // disabled 的不觸發
    let page = $(this).data("page");
    if (page) loadMediaArticles(page);
});

// 初始載入
document.addEventListener("DOMContentLoaded", () => {
    loadMediaArticles(1);
});

// 動態產生並插入 ItemList 結構化資料
function updateItemListSchema(articles) {
    // 移除舊的 schema 以免切換分頁時重複添加
    const oldSchema = document.getElementById('dynamic-itemlist-schema');
    if (oldSchema) {
        oldSchema.remove();
    }

    if (!articles || articles.length === 0) return;

    // 將 API 拿到的文章陣列轉換成 ItemList 需要的格式
    const itemListElements = articles.map((article, index) => {
        // 確保網址是絕對路徑
        const absoluteUrl = new URL(article.url || '#', window.location.origin).href;
        
        return {
            "@type": "ListItem",
            "position": index + 1,
            "url": absoluteUrl,
            "name": article.title || '媒體報導'
        };
    });

    const schemaData = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": itemListElements
    };

    // 建立 <script> 標籤並塞入 <head>
    const script = document.createElement('script');
    script.id = 'dynamic-itemlist-schema';
    script.type = 'application/ld+json';
    script.text = JSON.stringify(schemaData);
    document.head.appendChild(script);
}