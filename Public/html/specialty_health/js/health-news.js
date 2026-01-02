function loadHealthNews(page = 1) {
    fetch(`/specialty_health/api/health-news/?page=${page}`)
        .then(res => {
            if (!res.ok) throw new Error("API 錯誤：" + res.status);
            return res.json();
        })
        .then(data => {
            const container = document.getElementById("news-list");
            container.innerHTML = "";

            // （data.news 為空時）
            if (!data.news || data.news.length === 0) {
                container.innerHTML = `
                    <div class="col-12 text-center my-5">
                        <p class="text-muted mb-0 h3">暫無最新消息</p>
                    </div>
                `;
                document.getElementById("pagination-list").innerHTML = "";
                return;
            }

            data.news.forEach(item => {
                container.innerHTML += `
                    <div class="col-md-6 col-lg-4 col-xl-3 mb-4">
                        <a href="${item.url}">
                            <figure class="card h-100 shadow-sm article-card fade-in-card">
                                <figcaption class="card-body d-flex flex-column">
                                    <h5 class="card-title">${item.title}</h5>
                                    <small class="text-muted mt-auto">發布日期：${item.date}</small>
                                </figcaption>
                            </figure>
                        </a>
                    </div>
                `;
            });

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
                        <select id="news-page-select" class="form-control form-control-sm h-100" style="width:auto; display:inline-block;">
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
                document.getElementById("news-page-select").addEventListener("change", function() {
                    loadHealthNews(this.value);
                });
            }
        })

        // （API 出錯時）
        .catch(err => {
            console.error("[health-news] API 載入失敗：", err);
            const container = document.getElementById("news-list");
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
    if ($(this).parent().hasClass("disabled")) return;
    let page = $(this).data("page");
    if (page) loadHealthNews(page);
});

// 預設載入
document.addEventListener("DOMContentLoaded", () => {
    loadHealthNews(1);
});