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

                items.forEach((item, index) => {
                    if (item.is_group && item.children && item.children.length > 0) {
                        // --- 處理分組 (摺疊選單) ---
                        const groupId = `collapse-${index}`;
                        const isAnyChildActive = item.children.some(child => isActiveFn(child));

                        // 1. 建立 Parent Toggle 連結
                        const parentLink = document.createElement('a');
                        parentLink.className = `list-group-item list-group-item-action d-flex justify-content-between align-items-center ${isAnyChildActive ? 'parent-active' : ''}`;
                        parentLink.href = `#${groupId}`;
                        parentLink.setAttribute('data-toggle', 'collapse');
                        parentLink.setAttribute('aria-expanded', isAnyChildActive ? 'true' : 'false');
                        parentLink.innerHTML = `
                            <span>${renderTextFn(item)}</span>
                            <i class="fas fa-chevron-down nav-arrow"></i>
                        `;
                        list.appendChild(parentLink);

                        // 2. 建立 Collapse 內容容器
                        const collapseDiv = document.createElement('div');
                        collapseDiv.id = groupId;
                        collapseDiv.className = `collapse ${isAnyChildActive ? 'show' : ''}`;
                        
                        item.children.forEach(child => {
                            const childLink = document.createElement('a');
                            childLink.className = 'list-group-item list-group-item-action sub-item';
                            
                            if (child.pdf_url) {
                                childLink.href = child.pdf_url;
                                childLink.rel = 'noopener noreferrer';
                            } else {
                                childLink.href = buildHrefFn(child);
                            }
                            
                            childLink.innerHTML = `— ${child.title}`;
                            if (isActiveFn(child)) {
                                childLink.classList.add('active');
                            }
                            collapseDiv.appendChild(childLink);
                        });
                        list.appendChild(collapseDiv);

                    } else {
                        // --- 處理一般項目 (單一連結) ---
                        const link = document.createElement('a');
                        
                        if (item.pdf_url) {
                            link.href = item.pdf_url;
                            link.rel = 'noopener noreferrer';
                        } else {
                            link.href = buildHrefFn(item);
                        }
                        
                        link.className = 'list-group-item list-group-item-action';
                        link.innerHTML = renderTextFn(item);

                        if (isActiveFn(item)) {
                            link.classList.add('active');
                        }

                        list.appendChild(link);
                    }
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