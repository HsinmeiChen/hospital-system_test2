function loadHealthEdu(page = 1) {
    fetch(`/neuro-center/api/neuro-edu/?page=${page}`)
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
                const titleId = item.titleId || (item.images && item.images.length > 0 ? item.images[0].split('/').pop().split('_page')[0] : '');
                const detailUrl = `/neuro-center/neuro-edu/${titleId}/`;
                const imageUrl = item.images && item.images.length > 0 ? item.images[0] : '/Public/apps/neurology_center/images/default_article.jpg';

                container.innerHTML += `
                    <div class="col-md-6 col-lg-4 col-xl-3 mb-5 d-flex align-items-stretch">
                        <a href="${detailUrl}" class="w-100" style="text-decoration:none; color:inherit; display:block;">
                            <article class="magazine-card">
                                <div class="magazine-img-wrapper">
                                    <img src="${imageUrl}" loading="lazy" alt="${item.title}" onerror="this.src='/Public/apps/neurology_center/images/default_article.jpg'">
                                </div>
                                <div class="magazine-content">
                                    <div class="magazine-meta">Health Education</div>
                                    <h5 class="magazine-title">${item.title}</h5>
                                    <div class="magazine-read-more">READ MORE</div>
                                </div>
                            </article>
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
                    <li class="page-item ${current === 1 ? 'disabled' : ''} mx-1">
                        <a class="page-link page-btn nav-btn" href="#" data-page="1" style="border:none; border-radius:50%;"><i class="fas fa-angle-double-left"></i></a>
                    </li>
                `;
                // 上一頁
                pagination.innerHTML += `
                    <li class="page-item ${current === 1 ? 'disabled' : ''} mx-1">
                        <a class="page-link page-btn nav-btn" href="#" data-page="${current - 1}" style="border:none; border-radius:50%;"><i class="fas fa-angle-left"></i></a>
                    </li>
                `;
                // 下拉選單
                let selectHtml = `
                    <li class="page-item mx-2 d-flex align-items-center">
                        <select id="edu-page-select" class="form-select form-select-sm page-select" style="border-radius: var(--radius-xl); padding-left: 1rem; padding-right: 2rem; cursor: pointer;">
                `;
                for (let i = 1; i <= total; i++) {
                    selectHtml += `<option value="${i}" ${i === current ? 'selected' : ''}>第 ${i} 頁</option>`;
                }
                selectHtml += `</select></li>`;
                pagination.innerHTML += selectHtml;
                // 下一頁
                pagination.innerHTML += `
                    <li class="page-item ${current === total ? 'disabled' : ''} mx-1">
                        <a class="page-link page-btn nav-btn" href="#" data-page="${current + 1}" style="border:none; border-radius:50%;"><i class="fas fa-angle-right"></i></a>
                    </li>
                `;
                // 最後頁
                pagination.innerHTML += `
                    <li class="page-item ${current === total ? 'disabled' : ''} mx-1">
                        <a class="page-link page-btn nav-btn" href="#" data-page="${total}" style="border:none; border-radius:50%;"><i class="fas fa-angle-double-right"></i></a>
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