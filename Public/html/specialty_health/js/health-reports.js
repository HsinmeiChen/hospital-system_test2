function loadMediaArticles(page = 1) {
    fetch(`/specialty_health/api/health-media/?page=${page}`)
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

            data.articles.forEach(article => {
                container.innerHTML += `
                    <div class="col-md-6 col-lg-4 col-xl-3 mb-4">
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