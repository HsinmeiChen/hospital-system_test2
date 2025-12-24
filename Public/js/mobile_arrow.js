$(document).ready(function(){
    $(".vn-click").click(function(){
        $(".vn-info").slideToggle();
        $("i", this).toggleClass("fas fa-caret-down fas fa-caret-right");
    });
});	