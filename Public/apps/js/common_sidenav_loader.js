// ■■■■■■■■ 作用：讀取側邊選單 ■■■■■■■■
document.addEventListener("DOMContentLoaded", function () {
    function loadSidenav({ apiUrl, containerId, isActiveFn, renderTextFn, buildHrefFn, listClass = 'list-group', itemClass = 'list-group-item list-group-item-action', activeClass = 'active' }) {
        const container = document.getElementById(containerId);
        if (!container) return;

        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                const list = document.createElement('div');
                if (listClass) {
                    list.className = listClass;
                }

                const items = data.doctors || data.treatments || [];

                items.forEach(item => {
                    const link = document.createElement('a');
                    link.href = buildHrefFn(item);
                    if (itemClass) {
                        link.className = itemClass;
                    }
                    link.innerHTML = renderTextFn(item);

                    if (isActiveFn(item)) {
                        link.classList.add(activeClass);
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