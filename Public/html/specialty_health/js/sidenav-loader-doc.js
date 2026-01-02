// ■■■■■■■■ 共用函式：讀取側邊選單 (若有大量頁需用到，再放到 base.html) ■■■■■■■■
document.addEventListener("DOMContentLoaded", function () {
    function loadSidenav({ apiUrl, containerId, isActiveFn, renderTextFn, buildHrefFn }) {
        const container = document.getElementById(containerId);
        if (!container) return;

        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                // 清空容器
                container.innerHTML = '';

                // 遍歷科別
                const departments = data.departments || [];
                departments.forEach(department => {
                    // 建立科別標題
                    // const departmentTitle = document.createElement('h3');
                    // departmentTitle.className = 'sidenav-department';
                    // departmentTitle.textContent = department.department;
                    // container.appendChild(departmentTitle);

                    // 建立醫師列表
                    const list = document.createElement('div');
                    list.className = 'list-group';

                    department.doctors.forEach(doctor => {
                        const link = document.createElement('a');
                        link.href = buildHrefFn(doctor);
                        link.className = 'list-group-item list-group-item-action';
                        link.innerHTML = renderTextFn(doctor);

                        if (isActiveFn(doctor)) {
                            link.classList.add('active');
                        }

                        list.appendChild(link);
                    });

                    container.appendChild(list);
                });
            })
            .catch(err => {
                container.innerHTML = "<p>無法載入選單</p>";
                console.error(`載入 ${apiUrl} 發生錯誤：`, err);
            });
    }

    // 輸出到全域（供其他 script 呼叫）
    window.loadSidenav = loadSidenav;
});