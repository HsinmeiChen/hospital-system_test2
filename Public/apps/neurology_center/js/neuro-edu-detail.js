document.addEventListener('DOMContentLoaded', function () {
    // 直接從模板中取得資料（Django 已在 render() 時傳入）
    const images = window.eduImages || [];  // 從 Django 模板傳入
    const title = window.eduTitle || '';
    
    const container = document.getElementById('edu-article');
    if (container.innerHTML.trim() !== "") {
        console.log("Content already rendered by server.");
        return;
    }

    if (!images || images.length === 0) {
        document.getElementById('edu-article').innerHTML = '<p class="alert alert-warning">找不到該衛教文章</p>';
        return;
    }

    renderEduContent(images);

    function renderEduContent(images) {
        const container = document.getElementById('edu-article');
        container.innerHTML = '';

        images.forEach((img, index) => {
            const imgElement = document.createElement('img');
            imgElement.src = img;
            imgElement.className = 'img-fluid w-100 mb-3';
            imgElement.alt = `${title} - 頁面 ${index + 1}`;
            container.appendChild(imgElement);
        });
    }
});