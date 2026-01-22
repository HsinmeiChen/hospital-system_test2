// 共用函式：主要處理網頁剛開始載入時不含 modal，當使用者點擊才會出現，關閉 modal 也會從 DOM 移除
// 用意：影音 Modal 結構與 iframe 不預載入，DOM 更小 / iframe 僅在點擊時載入 / Modal 區塊關閉即消失 (減少 DOM 元素長駐、避免記憶體占用)
function openVideoModal(url, title) {
    // 如果 modal 已存在就先移除（防止重複）
    $('#videoModal').remove();

    // 動態產生 Modal HTML 結構
    const modalHtml = `
    <div class="modal fade" id="videoModal" tabindex="-1" role="dialog" aria-labelledby="videoTitle" aria-hidden="true">
        <div class="modal-dialog modal-xl modal-dialog-centered" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <!-- <h5 class="modal-title" id="videoTitle">${title}</h5> -->
                    <button type="button" class="close" data-dismiss="modal" aria-label="關閉">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="embed-responsive embed-responsive-16by9">
                        <iframe id="videoFrame" class="embed-responsive-item" src="${url}" title="${title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `;
    $('body').append(modalHtml);
    $('#videoModal').modal('show');

    // 當 Modal 關閉後，將整個 #videoModal DOM 元素從頁面中移除，連帶 <iframe> 也一併被移除，達成「清空影片、停止播放」的效果
    $('#videoModal').on('hidden.bs.modal', function () {
        $('#videoModal').remove();
    });
}