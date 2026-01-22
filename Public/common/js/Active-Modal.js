var elements = $('.Pure-modal-overlay, .Pure-modal');
// $('button').click(function(){
//     elements.addClass('active');
// });
$('.act_modal').click(function(){
    elements.addClass('active');
});
$('.Pure-close-modal, .clx-modal').click(function(){
    elements.removeClass('active');
});


// 參考網址：https://codepen.io/nainoashizuru/pen/PwJZVa/