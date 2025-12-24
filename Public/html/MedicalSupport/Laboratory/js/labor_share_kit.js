$(function () {
    // *==== 檢驗科頁首、頁尾 ====* //
    $(".head_nav").load("header_labor.html"); 
    $(".foot_content").load("../../../footer.html");    

    // 用一個類似目錄頁，再利用選單來點選時，載入各對應的頁面內容。===== *
    $(".side_menu>a").click(function (e) {
        $(".side_menu>a.activeed").removeClass();
        $(".content").load($(this).addClass("activeed").attr("href"));
        e.preventDefault();
    }).first().click();
});


// $(function () {
//     $(".side_menu").load("Health_Edu_menu.html", function () {
//         var url = location.href;                           // 宣告url變數 = 目前瀏覽器網址
//         var href = url.substr(url.lastIndexOf("/") + 1);   // 宣告href變數 = 擷取 url 字元
//         $(".side_menu_div li a[href='" + (href || "Health_Edu_index.html") + "']").addClass("activeed");
//         $(".sidemenu-items > a[href='" + (href || "Health_Edu_index.html") + "']").parent().parent(".collapse").addClass("show");
//         $('.collapse').on('shown.bs.collapse', function () {
//             $(this).siblings().find("[role=button]").attr("aria-expanded","true");
//         });
//         $(".sidemenu-items > a[href='" + (href || "Health_Edu_index.html") + "']").collapse({
//             // parent : '#accordion',
//             toggle : true,            
//         });      
//     });
//     $(".health_edu").load("../../../bread_pencil.html .health_edu>a");
// });