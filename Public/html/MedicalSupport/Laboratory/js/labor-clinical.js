// $(function () { 
//     // ===== 使用外部載入選單個別-menu 及 設定首頁，並判斷已點選哪個選單。===== *
//     $(".side_menu").load("labor-clinical-menu.html", function () {// 動態載入menu.html
//         //替目前頁面選項加上選取後效果
//         var url = location.href;                           // 宣告url變數 = 目前瀏覽器網址
//         var href = url.substr(url.lastIndexOf("/") + 1);   // 宣告href變數 = 擷取 url 字元
//         $(".side_menu li a[href='" + (href || "labor-clinical-index.html") + "']").addClass("activeed");  
//         //a元素判斷擷取的字元是否有效，無效就選是首頁的a元素，再套上CSS效果
//     });
// });

$(function () {
    $(".side_menu").load("labor-clinical-menu.html", function () {
        var url = location.href;                           // 宣告url變數 = 目前瀏覽器網址
        var href = url.substr(url.lastIndexOf("/") + 1);   // 宣告href變數 = 擷取 url 字元
        $(".side_menu_div li a[href='" + (href || "labor-clinical-index.html") + "']").addClass("activeed");
        $(".sidemenu-items > a[href='" + (href || "labor-clinical-index.html") + "']").parent().parent(".collapse").addClass("show");
        $('.collapse').on('shown.bs.collapse', function () {
            $(this).siblings().find("[role=button]").attr("aria-expanded","true");
        });
        $(".sidemenu-items > a[href='" + (href || "labor-clinical-index.html") + "']").collapse({
            // parent : '#accordion',
            toggle : true,            
        });      
    });
});

// 參考網址：https://garyissogood.github.io/jquery/jquery-application/20200315/2393945142/