$(function () {
    $("#nav_2").load("/Public/apps/Online_nav.html");
    // $(".online_nav_bg").load("Online_nav.html", function () {// 動態載入menu.html
    //         setTimeout(() => {
    //             //替目前頁面選項加上選取後效果
    //             var url = location.href;                           // 宣告url變數 = 目前瀏覽器網址
    //             var href = url.substr(url.lastIndexOf("/") + 1);   // 宣告href變數 = 擷取 url 字元
    //             if (href == 'OnlineReg') {
    //                 href = 'Patient_Guide_2.html';
    //             }
    //             $(".online_nav_bg div a[href='" + (href || "Patient_Guide_2.html") + "']").addClass("active");
    //             //a元素判斷擷取的字元是否有效，無效就選是首頁的a元素，再套上CSS效果
    //         }, 200);
    //     });
});