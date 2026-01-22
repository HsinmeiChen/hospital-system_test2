$(function () {
    // ===== 使用外部載入選單個別-menu 及 設定首頁，並判斷已點選哪個選單。===== *

    $(".side_menu").load("labor-pathology-menu.html", function () {// 動態載入menu.html
        //替目前頁面選項加上選取後效果
        var url = location.href;                           // 宣告url變數 = 目前瀏覽器網址
        var href = url.substr(url.lastIndexOf("/") + 1);   // 宣告href變數 = 擷取 url 字元
        $(".side_menu li a[href='" + (href || "labor-pathology-index.html") + "']").addClass("activeed");  
        //a元素判斷擷取的字元是否有效，無效就選是首頁的a元素，再套上CSS效果
    });

});


// $(function () {
//     $(".side_menu").load("test-ajax-menu.html", function () {// 動態載入menu.html
//         //替目前頁面選項加上選取後效果
//         var url = location.href;                           // 宣告url變數 = 目前瀏覽器網址
//         var href = url.substr(url.lastIndexOf("/") + 1);   // 宣告href變數 = 擷取 url 字元
//         $("a[href='" + (href || "test-ajax-index.html") + "']").addClass("activeed");  
//         //a元素判斷擷取的字元是否有效，無效就選是首頁的a元素，再套上CSS效果
//     });
// });

// $(function () {
//     $(".menu>a").click(function (e) {
//     $(".menu>a.selected").removeClass();
//     $(".content").load($(this).addClass("selected").attr("href"));
//     e.preventDefault();
//     }).first().click();
// });


// 參考網址：https://garyissogood.github.io/jquery/jquery-application/20200315/2393945142/