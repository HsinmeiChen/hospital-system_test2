// ■■■■■■■■■■■■■■■■■■■■■■■■■■ 停休診時間 ■■■■■■■■■■■■■■■■■■■■■■■■■■

$(document).ready(function () {
$('.open-stop-modal').on('click', function () {
    const empId = $(this).data('id');
    const name = $(this).data('name');

    // 移除舊的 modal（防止重複）
    $('#stopModal').remove();

    // 建立 modal HTML 並插入 body
    const modalHtml = `
    <div class="modal fade" id="stopModal" tabindex="-1" role="dialog" aria-labelledby="stopModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 class="modal-title" id="stopModalLabel"><strong>${name}</strong> <small>醫師 - 停休診時間</small></h4>
                    <button type="button" class="close" data-dismiss="modal" aria-label="關閉">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                </div>
                <div class="modal-body clinic-rest-time" id="modal-body-content">
                    <p>載入中...</p>
                    <div class="row"></div>
                </div>
            </div>
        </div>
    </div>
    `;
    $('body').append(modalHtml); // 將 modal 動態插入到 <body>

    // Ajax 載入資料
    $.ajax({
        url: `/neuro-center/api/stop-info/${empId}/`,
        method: 'GET',
        success: function (data) {
            const $modalBody = $('#modal-body-content');
            if (data.stop_info && Object.keys(data.stop_info).length > 0) {
                let content = '';
                $.each(data.stop_info, function (month, items) {
                content += `
                    <table class="table">
                    <tr>
                        <td class="clinic-month">
                        <h6>
                            <div>${month.slice(5, 7)}月</div>
                            <div>${month.slice(0, 4)}年</div>
                        </h6>
                        </td>
                        <td class="py-0">
                        <table class="table mb-0">
                            <tr>
                            <td class="clinic-time-list">
                                <ul class="list-group list-group-flush">
                                <li class="list-group-item">
                                    <div class="title">
                                    <div>日期</div><div>診別</div><div>診間</div>
                                    </div>
                                </li>`;
                $.each(items, function (i, item) {
                    const badgeClass = item.period === '早診' ? 'morning-clinic'
                                    : item.period === '午診' ? 'afternoon-clinic'
                                    : item.period === '晚診' ? 'evening-clinic' : '';
                    content += `
                    <li class="list-group-item">
                        <div class="detail">
                        <div>${item.date}</div>
                        <div class="badge ${badgeClass}">${item.period}</div>
                        <div>${item.room.slice(1, 4)} 診</div>
                        </div>
                    </li>`;
                });
                content += '</ul></td></tr></table></td></tr></table>';
            });
                $modalBody.html(content);
            } else {
                $modalBody.html('<p class="no-data-text">目前無資料。</p>');
            }
        },
        error: function () {
            $('#modal-body-content').html('<p class="no-data-text">資料載入失敗。</p>');
        }
    });        
        // 顯示 modal（一定要等 append 完才呼叫）
        const modalInstance = new bootstrap.Modal(document.getElementById('stopModal'));
        modalInstance.show();
    });
});


// ■■■■■■■■■■■■■■■■■■■■■■■■■■ 分頁功能 (切換不刷新，不具有最前/後一頁功能) ■■■■■■■■■■■■■■■■■■■■■■■■■■

function initAjaxCardPagination(config) {
    const {
        apiUrl, // 後端 API 路徑
        containerId, // 資料要插入的 HTML 區塊容器（例：related-articles-container）
        paginationId, // 分頁按鈕容器（例：pagination）
        perPage = 3, // 每頁顯示幾筆，預設 3 筆
        renderItem  // 一個「客製化」函式，負責渲染每一筆資料的 HTML
    } = config;

    // 取得 DOM 元素：資料容器與分頁容器
    const container = document.getElementById(containerId);
    const pagination = document.getElementById(paginationId);

    function loadPage(page = 1) { // 宣告一個內部函式 loadPage()，預設載入第 1 頁
    fetch(`${apiUrl}?page=${page}&per_page=${perPage}`)
        .then(res => res.json())
        .then(data => {
        // 每次載入前清空畫面上的資料與分頁
        container.innerHTML = '';
        pagination.innerHTML = '';

        // 後端可能回傳 articles 或 videos，這裡用「有就用、沒有就用空陣列」方式處理
        const items = data.articles || data.videos || [];

        // 逐筆跑資料，並用 renderItem() 這個自定義函式產出 HTML，插入畫面中
        items.forEach(item => {
            container.innerHTML += renderItem(item);
        });

        // 如果只有一頁或沒有資料，就不顯示分頁
        if (data.num_pages <= 1) return;

        const current = data.current_page;
        const total = data.num_pages;
        let html = '';

        // 第一頁
        html += `
            <li class="page-item ${current === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="1">&laquo;</a>
            </li>
        `;

        // 上一頁
        html += `
            <li class="page-item ${current === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${current - 1}">&lsaquo;</a>
            </li>
        `;

        // 下拉選單頁碼切換
        let selectHtml = `
            <li class="page-item">
                <select class="form-control page-select">
        `;
        for (let i = 1; i <= total; i++) {
            selectHtml += `<option value="${i}" ${i === current ? 'selected' : ''}>第 ${i} 頁 / 共 ${total} 頁</option>`;
        }
        selectHtml += `</select></li>`;
        html += selectHtml;

        // 下一頁
        html += `
            <li class="page-item ${current === total ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${current + 1}">&rsaquo;</a>
            </li>
        `;

        // 最後頁
        html += `
            <li class="page-item ${current === total ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${total}">&raquo;</a>
            </li>
        `;

        pagination.innerHTML = html;

        // 綁定事件
        $(pagination).find('.page-link').on('click', function(e) {
            e.preventDefault();
            if ($(this).parent().hasClass('disabled')) return;
            const page = $(this).data('page');
            if (page) loadPage(page);
        });

        $(pagination).find('.page-select').on('change', function() {
            loadPage(parseInt($(this).val()));
        });
        });
    }

    loadPage(); // 預設載入第 1 頁
}


// ■■■■■■■■■■■■■■■■■■■■■■■■■■ 相關文章、影音專區 ■■■■■■■■■■■■■■■■■■■■■■■■■■

document.addEventListener('DOMContentLoaded', function () {
    // const employeeId = "{{ employee_id }}"; // 放在 HTML 中沒問題，在 JS 檔案中無效：它只是會變成一個字串 "{{ employee_id }}"，Django 不會幫你轉換。
    const employeeId = document.getElementById('doctor-main').dataset.employeeId; // 若從獨立 JS 檔案引入，建議從 HTML 傳值

    // ========== 相關文章 ==========
    initAjaxCardPagination({
        apiUrl: `/neuro-center/api/doctor/${employeeId}/articles/`,
        containerId: "related-articles-container",
        paginationId: "pagination",
        perPage: 2,
        renderItem: function (article) {
        return `
            <div class="h-100">
                <a href="${article.url}" class="text-decoration-none d-block h-100">
                    <figure class="article-card h-100 m-0">
                        <div class="article-img-wrapper">
                            <img src="/media/${article.image}" class="article-img" loading="lazy" alt="${article.title}">
                        </div>
                        <figcaption class="article-content">
                            <h4 class="article-title">${article.title}</h4>
                            <p class="text-sm line-clamp-2">${article.summary}...</p>
                        </figcaption>
                    </figure>
                </a>
            </div>
        `;
        }
    });

    // ========== 影音專區 ==========
    initAjaxCardPagination({
        apiUrl: `/neuro-center/video-section/${employeeId}/`,
        containerId: "related-videos-container",
        paginationId: "video-pagination",
        perPage: 3,
        renderItem: function (video) {
        return `
            <div class="video-card">
                <button class="open-video-modal h-full" data-toggle="modal" data-target="#videoModal" data-title="${video.ytb_title}" data-date="${video.ytb_date}" data-url="${video.ytb_url}">
                    <figure class="video-card">
                        <img class="h-full object-cover" src="${video.thumb_url}" alt="${video.ytb_title}">
                        <div class="video-overlay">
							<span class="material-symbols-outlined text-5xl video-icon" data-icon="play_circle">play_circle</span>
						</div>
                        <figcaption class="video-caption">
                            <p class="text-white text-sm font-bold truncate">${video.ytb_title}</p>                            
                        </figcaption>
                    </figure>
                </button>
            </div>
        `;
        }
    });
});


// 因為是 BS 的套件語法，所以不能跟其他 JS 檔案混用。
// resetVideo-停止影片播放並釋放資源，避免關閉 Modal 後影片仍在背景播放。
function resetVideo() {
    $('#videoFrame').attr('src', '');
}  
// 開啟 Modal 時，設定影片標題、日期與 YouTube 連結
$('#videoModal').on('show.bs.modal', function (event) {
    const button = $(event.relatedTarget);
    const title = button.data('title');
    const date = button.data('date');
    const url = button.data('url');

    const modal = $(this);
    modal.find('.modal-title').text(title);
    modal.find('#videoModalDate').text(date);
    modal.find('#videoFrame').attr('src', url);
});
// 關閉 Modal 時，清除影片的 <iframe> src → 停止播放
$('#videoModal').on('hidden.bs.modal', resetVideo);



// ■■■■■■■■■■■■■■■■■■■■■■■■■ 醫師側邊選單 ■■■■■■■■■■■■■■■■■■■■■■■■■

document.addEventListener("DOMContentLoaded", function () {
    const currentDoctorId = document.getElementById('doctor-main') ? String(document.getElementById('doctor-main').dataset.employeeId) : '';

    window.loadSidenav({
        apiUrl: '/neuro-center/api/doctor_sidenav/',
        containerId: 'doctor-sidenav',
        listClass: 'flex flex-col gap-sm w-full',
        itemClass: 'doctor-btn text-decoration-none',
        activeClass: 'is-active',
        isActiveFn: item => String(item.employee_id) === currentDoctorId,
        buildHrefFn: item => `/neuro-center/doctor/${item.employee_id}/`,
        renderTextFn: item => `
            <span class="material-symbols-outlined" data-icon="person">person</span>
            <div style="font-size: 1.2rem; letter-spacing: 0.01em; font-weight: 600;"><div style="font-size: .8rem;font-weight:500;">${item.job_title}</div>${item.name}</div>
        `
    });
});



