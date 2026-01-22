// ■■■■■■■■■■■■■■■■■■■■■■■■■■ 側邊隨機 5 筆文章 ■■■■■■■■■■■■■■■■■■■■■■■■■■
function loadRandomHealthReports() {
    fetch('/specialty_health/api/random_health_reports/')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('random-health-reports');
            container.innerHTML = '';
            data.articles.forEach(article => {

                // 先建立外層 div
                const wrapper = document.createElement('div');
                wrapper.className = 'col-md-6 col-xl-12';

                // 建立 figure                
                const card = document.createElement('figure');
                card.className = 'card mb-4 health-report-card shadow-sm fade-in-card article-card';
                card.style.cursor = 'pointer';
                card.innerHTML = `
                    <div class="img-container">
                        <img src="/media/${article.image}" class="card-img-top" alt="${article.title}">
                    </div>
                    <figcaption class="card-body p-2">
                        <h5 class="card-title" style="padding: 0 5px;font-size:.9rem;">${article.title}</h5>
                        <!--<small class="text-muted">發表於 ${article.pub_date}</small>-->
                    </figcaption>
                `;

                // 點擊直接跳轉頁面（刷新並更新網址）
                card.onclick = function() {
                    window.location.href = `/specialty_health/articles/${article.filename}/`;
                };

                // 把 figure 放進外層 div
                wrapper.appendChild(card);

                // 再把外層 div 丟進 container
                container.appendChild(wrapper);
            });
        });
}

document.addEventListener('DOMContentLoaded', loadRandomHealthReports);