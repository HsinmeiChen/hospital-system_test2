// 清空重填文字
$(document).ready(function(){
    $('#reset_btn').click(function(){				
        // if(confirm("Want to clear?")){
            /*Clear all input type="text" box*/
            // $('#form1 input[type="text"]').val('');
            /*Clear textarea using id */
            $('#contact_us textarea').val('');
        // }					
    });
});
// 輸入文字後才會打開送出按鈕
$(document).ready(function() {
    $('#submit').attr('disabled', true);    
    $('input[type="date"],input[type="time"],textarea').on('keyup',function() {
        var textarea_value = $("#msgus").val();
        var text_value = $('input[type="date"],input[type="time"]').val();
        
        if(textarea_value != '' && text_value != '') {
            $('#submit').attr('disabled', false);
        } else {
            $('#submit').attr('disabled', true);
        }
    });
});