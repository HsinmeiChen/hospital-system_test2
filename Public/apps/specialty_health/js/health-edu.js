function loadHealthEdu(page = 1) {
    fetch(`/specialty_health/api/health-edu/?page=${page}`)
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
                let imgs = item.images.map(img => `<img src="${img}" class="img-fluid mb-3 w-100">`).join('');
                container.innerHTML += `
                    <div class="col-md-6 col-lg-4 col-xl-3 mb-4">
                        <figure class="card h-100 article-card fade-in-card" data-toggle="modal" data-target="#modal-${idx}">
                            <div class="img-container">
                                <img src="${item.images[0]}" loading="lazy" alt="${item.title}"/>
                            </div>
                            <figcaption class="card-body justify-content-center">
                                <h5 class="card-title">${item.title}</h5>
                            </figcaption>
                        </figure>
                        <div class="modal fade" id="modal-${idx}" tabindex="-1" role="dialog">
                            <div class="modal-dialog modal-lg modal-dialog-centered" role="document">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h5 class="modal-title">${item.title}</h5>
                                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                                    </div>
                                    <div class="modal-body">${imgs}</div>
                                </div>
                            </div>
                        </div>
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