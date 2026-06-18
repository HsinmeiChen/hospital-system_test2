function loadMediaArticles(page = 1) {
    fetch(`/neuro-center/api/neuro-media/?page=${page}`)
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
                return;
            }

            if (data.articles && data.articles.length > 0) {
                let html = '<div class="newspaper-grid">';
                
                data.articles.forEach((article, index) => {
                    const pubDate = article.pub_date || '';
                    const title = article.title || '';
                    const summary = article.summary || '';
                    const img = `/media/${article.image}`;
                    const url = article.url || '#';

                    // 採用 10 篇一循環的報紙排版
                    const patternIndex = index % 10;

                    if (patternIndex === 0 || patternIndex === 6) {
                        // 1. 頭條大版面 (The Lead Story) - Span 2x2
                        html += `
                            <a href="${url}" class="np-card np-hero">
                                <img src="${img}" alt="${title}" loading="lazy">
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
                                <img src="${img}" alt="${title}" loading="lazy">
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
                                <img src="${img}" alt="${title}" loading="lazy">
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
                                <img src="${img}" alt="${title}" loading="lazy">
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
                                <img src="${img}" alt="${title}" loading="lazy">
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
                                <img src="${img}" alt="${title}" loading="lazy">
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