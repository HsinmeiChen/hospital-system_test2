document.addEventListener("DOMContentLoaded", function () {
    // 原寫法：因抓到空字串，無法有 active 的效果
    // const currentUrlName = window.location.pathname.split('/').pop();
    // 此寫法可排除末尾空字串，即使網址有斜線結尾也不會抓到空字串
    const pathSegments = window.location.pathname.split('/').filter(Boolean);
    const currentUrlName = pathSegments[pathSegments.length - 1];
    

    window.loadSidenav({
        apiUrl: '/neuro-center/api/neuro-treatment/sidenav/',
        containerId: 'treatment-sidenav',
        isActiveFn: item => currentUrlName.toLowerCase() === item.url_name.toLowerCase(), // 準確判斷目前網址對應哪個項目
        // isActiveFn: item => currentUrlName.includes(item.url_name), // inclides 方法可能會導致錯誤匹配，會有多個 active 的情況
        buildHrefFn: item => `/neuro-center/neuro-treatment/${item.url_name}`,
        renderTextFn: item => `${item.title}`
    });
});