// ■■■■■■■■■■■■■■■■■■■■■■■■■■ 影音專區 Health Films ■■■■■■■■■■■■■■■■■■■■■■■■■■
// 動態載入影片列表
function loadVideos(page=1) {
    $.get('/specialty_health/api/health-film-api/', { page: page }, function(res) {
        let videoList = $('#video-list');
        videoList.empty();

        if (res.videos.length === 0) {
            videoList.append(`
                <div class="col-12 text-center my-5">
                    <p class="text-muted">目前暫無影音文章</p>
                </div>
            `);
            $('#pagination').empty(); // 沒有影片就不顯示分頁
            return;
        }

        res.videos.forEach(v => {
            videoList.append(`
                <div class="col-md-6 col-lg-4 col-xl-3 mb-4">
                    <figure class="card video-card h-100 shadow-sm article-card fade-in-card" data-url="${v.youtube_url}">
                        <img src="${v.youtube_image}" class="card-img-top" alt="${v.title}">
                        <figcaption class="card-body">
                            <small class="card-text text-muted">上架時間：${v.date}</small>
                            <h5 class="card-title">${v.title}</h5>                            
                        </figcaption>
                    </figure>
                </div>
            `);
        });

        // 分頁控制
        let pagination = $('#pagination');
        pagination.empty();

        if (res.total_pages > 1) {
            let current = res.current_page;
            let total = res.total_pages;

            // 第一頁
            pagination.append(`
                <li class="page-item ${current === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="1">&laquo;</a>
                </li>
            `);

            // 上一頁
            pagination.append(`
                <li class="page-item ${current === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="${current - 1}">&lsaquo;</a>
                </li>
            `);

            // 下拉選單
            let selectHtml = `
                <li class="page-item">
                    <select id="video-page-select" class="form-control form-control-sm h-100" style="width:auto; display:inline-block;">
            `;
            for (let i = 1; i <= total; i++) {
                selectHtml += `<option value="${i}" ${i === current ? 'selected' : ''}>第 ${i} 頁</option>`;
            }
            selectHtml += `</select></li>`;
            pagination.append(selectHtml);

            // 下一頁
            pagination.append(`
                <li class="page-item ${current === total ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="${current + 1}">&rsaquo;</a>
                </li>
            `);

            // 最後頁
            pagination.append(`
                <li class="page-item ${current === total ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="${total}">&raquo;</a>
                </li>
            `);

            // 綁定下拉事件
            $('#video-page-select').on('change', function() {
                loadVideos($(this).val());
            });

        }
    });
}

// 點擊分頁
$(document).on('click', '#pagination .page-link', function(e) {
    e.preventDefault();

    // 如果父元素是 disabled，就不觸發
    if ($(this).parent().hasClass('disabled')) return;

    // 確保頁碼是正確數字
    let page = $(this).data('page');
    if (page) loadVideos(page);
});

// 點擊影片開啟 Modal
$(document).on('click', '.video-card', function () {
    const url = $(this).data('url');
    const title = $(this).find('.card-title').text();
    openVideoModal(url, title);
});

// Modal 關閉時清空影片
$('#videoModal').on('hidden.bs.modal', function () {
    $('#videoFrame').attr('src', '');
});

// 預設載入
$(document).ready(() => loadVideos());