function loadHealthEdu(page = 1) {
    fetch(`/breast-care-center/api/breast-edu/?page=${page}`)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById("edu-list");
            container.innerHTML = "";

            // （data.news 為空時）
            if (!data.items || data.items.length === 0) {
                container.innerHTML = `<div class="col-12 text-center my-5"><p class="text-muted mb-0 h3">暫無資料</p></div>`;
                document.getElementById("pagination-list").innerHTML = "";
                return;
            }

            data.items.forEach((item, idx) => {
                // 若 API 已回傳 titleId，使用它；否則從第一張圖檔名取前綴
                const titleId = item.titleId || item.images[0].split('/').pop().split('_page')[0];
                const detailUrl = `/breast-care-center/breast-edu/${titleId}/`;
                container.innerHTML += `
                    <div class="col-md-6 col-lg-4 col-xl-3 mb-4">
                        <a href="${detailUrl}" class="edu-card-link">
                            <figure class="card h-100 shadow-sm article-card fade-in-card edu-card-custom">
                                <!-- Top Badge (Option C) -->
                                <div class="edu-card-badge">
                                    衛教資訊
                                </div>
                                <figcaption class="card-body d-flex align-items-center position-relative mt-2">
                                    <!-- Left Icon (Option A) -->
                                    <div class="edu-card-icon-left">
                                        <i class="fas fa-book-medical"></i>
                                    </div>
                                    
                                    <!-- Title -->
                                    <h5 class="card-title edu-card-title mb-0 flex-grow-1">${item.title}</h5>
                                    
                                    <!-- Right Arrow (Option B) -->
                                    <div class="edu-card-arrow-right">
                                        <i class="fas fa-arrow-right"></i>
                                    </div>
                                </figcaption>
                            </figure>
                        </a>
                    </div>

                    <!-- <div class="col-md-6 col-lg-4 col-xl-3 mb-4">
                        <a href="${detailUrl}" class="card-link" style="text-decoration:none;color:inherit;">
                            <figure class="card h-100 article-card fade-in-card">
                                <div class="img-container">
                                    <img src="${item.images[0]}" loading="lazy" alt="${item.title}">
                                </div>
                                <figcaption class="card-body justify-content-center">
                                    <h5 class="card-title">${item.title}</h5>
                                </figcaption>
                            </figure>
                        </a>
                    </div> -->
                `;
            });

            // 動態生成 SEO ItemList Schema
            const itemList = {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "itemListElement": data.items.map((item, idx) => {
                    const titleId = item.titleId || item.images[0].split('/').pop().split('_page')[0];
                    return {
                        "@type": "ListItem",
                        "position": idx + 1,
                        "url": window.location.origin + `/breast-care-center/breast-edu/${titleId}/`
                    };
                })
            };

            // 移除舊的動態 Schema (切換分頁時)
            const oldSchema = document.getElementById("dynamic-itemlist-schema");
            if (oldSchema) oldSchema.remove();

            // 注入新的 Schema 到 <head>
            if (data.items.length > 0) {
                const script = document.createElement("script");
                script.id = "dynamic-itemlist-schema";
                script.type = "application/ld+json";
                script.text = JSON.stringify(itemList);
                document.head.appendChild(script);
            }

            // 分頁控制
            const pagination = document.getElementById("pagination-list");
            pagination.innerHTML = "";

            const total = data.num_pages;
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
                        <select id="edu-page-select" class="form-control form-control-sm h-100" style="width:auto; display:inline-block;">
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
                // 下拉事件
                document.getElementById("edu-page-select").addEventListener("change", function() {
                    loadHealthEdu(this.value);
                });
            }
        })

        // （API 出錯時）
        .catch(err => {
            const container = document.getElementById("edu-list");
            container.innerHTML = `<div class="col-12 text-center my-5"><p class="text-danger mb-0 h3">資料載入失敗，請稍後再試。</p></div>`;
            document.getElementById("pagination-list").innerHTML = "";
        });
}

// 點擊分頁
$(document).on("click", "#pagination-list .page-link", function(e) {
    e.preventDefault();
    if ($(this).parent().hasClass("disabled")) return;
    let page = $(this).data("page");
    if (page) loadHealthEdu(page);
});

// 預設載入
document.addEventListener("DOMContentLoaded", () => {
    loadHealthEdu(1);
});