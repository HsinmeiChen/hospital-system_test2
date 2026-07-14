document.addEventListener("DOMContentLoaded", function () {
    const pathSegments = window.location.pathname.split('/').filter(Boolean);
    const currentUrlName = pathSegments[pathSegments.length - 1];
    
    window.loadSidenav({
        // 套用 HTML 傳過來的 API 變數
        apiUrl: API_URL_SIDENAV,
        containerId: 'treatment-sidenav',
        isActiveFn: item => currentUrlName.toLowerCase() === item.url_name.toLowerCase(),
        
        // 將佔位符 'PLACEHOLDER' 替換成真正的 url_name
        buildHrefFn: item => URL_TREATMENT_BASE.replace('PLACEHOLDER', item.url_name),
        
        renderTextFn: item => `${item.title}`
    });
});
