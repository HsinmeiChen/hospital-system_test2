// ■■■■■■■■ 共用函式：讀取側邊選單 (若有大量頁需用到，再放到 base.html) ■■■■■■■■
document.addEventListener("DOMContentLoaded", function () {
    function loadSidenav({ apiUrl, containerId, isActiveFn, renderTextFn, buildHrefFn }) {
        const container = document.getElementById(containerId);
        if (!container) return;

        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                const list = document.createElement('div');
                list.className = 'list-group';

                const items = data.doctors || data.treatments || [];

                items.forEach(item => {
                    const link = document.createElement('a');
                    
                    // ✅ 判斷是否有 PDF 連結
                    if (item.pdf_url) {
                        // 有 PDF：直接開啟，不導向文章頁
                        link.href = item.pdf_url;
                        // link.target = '_blank'; # 開新分頁
                        link.rel = 'noopener noreferrer';
                    } else {
                        // 沒有 PDF：使用原本的文章連結
                        link.href = buildHrefFn(item);
                    }
                    
                    link.className = 'list-group-item list-group-item-action';
                    link.innerHTML = renderTextFn(item);

                    if (isActiveFn(item)) {
                        link.classList.add('active');
                    }

                    list.appendChild(link);
                });

                container.innerHTML = '';
                container.appendChild(list);
            })
            .catch(err => {
                container.innerHTML = "<p>無法載入選單</p>";
                console.error(`載入 ${apiUrl} 發生錯誤：`, err);
            });
    }

    // 輸出到全域（供其他 script 呼叫）
    window.loadSidenav = loadSidenav;
});