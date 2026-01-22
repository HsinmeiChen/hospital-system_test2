$(function () {
    // ----首頁---- //
    $(".main_pencil").load("/Public/apps/bread_pencil.html .main_pencil>a");
    // ----網路掛號---- //
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
    $(".Online_Appointment").load("/Public/apps/bread_pencil.html .Online_Appointment>a");
    $(".Online_Appointment_part").load("/Public/apps/bread_pencil.html .Online_Appointment_part>a");
    $(".Online_Appointment_doc").load("/Public/apps/bread_pencil.html .Online_Appointment_doc>a");

    // ----科室總覽---- //
    $(".surgical_in").load("/Public/apps/bread_pencil.html .surgical_in>a");
    // ----檢驗科---- //
    $(".labor_pencil").load("/Public/apps/bread_pencil.html .labor_pencil>a");     //* 檢驗科首頁 *//
    $(".pencil_in").load("/Public/apps/bread_pencil.html .pencil_in>a");  //* 檢體採集衛教 *//
    $(".select_in").load("/Public/apps/MedicalSupport/Laboratory/ajax_labor_element.html .select_in>div");  //* 檢體採集衛教-下拉選項 *//
    $(".pencil_4").load("/Public/apps/bread_pencil.html .pencil_4>a");  //* 微生物培養檢體採集方法須知 *//
    $(".select_4").load("/Public/apps/MedicalSupport/Laboratory/ajax_labor_element.html .select_4>div");  //* 微生物培養檢體採集方法須知-下拉選項 *//
    $(".pencil_3").load("/Public/apps/bread_pencil.html .pencil_3>a");  //* 檢體採集原則 *//
    $(".select_3").load("/Public/apps/MedicalSupport/Laboratory/ajax_labor_element.html .select_3>div"); //* 檢體採集原則-下拉選項 *//
});

// *==== 網路掛號轉移用 ====*
function goDoctorPage(dn,sn) {
    const form = document.createElement('form');
    form.method = 'post';
    form.action = '/MedicalSupport/Patient_Guide/OnlineReg';

    const hiddenField1 = document.createElement('input');
    hiddenField1.type = 'hidden';
    hiddenField1.name = 'DN';
    hiddenField1.value = dn;
    form.appendChild(hiddenField1);
    const hiddenField2 = document.createElement('input');
    hiddenField2.type = 'hidden';
    hiddenField2.name = 'SN';
    hiddenField2.value = sn;
    form.appendChild(hiddenField2);
    const hiddenField3 = document.createElement('input');
    hiddenField3.type = 'hidden';
    hiddenField3.name = 'action';
    hiddenField3.value = 'doctor';
    form.appendChild(hiddenField3);

    document.body.appendChild(form);
    form.submit();
}

