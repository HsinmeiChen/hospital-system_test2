// 篩選內容 https://www.w3schools.com/jquery/jquery_filters.asp
$(document).ready(function(){
	// 我要看哪一科搜尋功能
    $("#search_box").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $(".which_class tbody tr").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
	// 看診進度搜尋功能
	$("#search_morning").on("keyup", function() {
		var value = $(this).val().toLowerCase();
		$(".morning_which_doc .Div_box").filter(function() {
			$(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
		});
	});
	$("#search_noon").on("keyup", function() {
		var value = $(this).val().toLowerCase();
		$(".noon_which_doc .Div_box").filter(function() {
			$(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
		});
	});
	$("#search_night").on("keyup", function() {
		var value = $(this).val().toLowerCase();
		$(".night_which_doc .Div_box").filter(function() {
			$(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
		});
	});
});

// 清除輸入框內容 https://www.itread01.com/content/1546258339.html
$("input").focus(function(){  
	$(this).parent().children(".input_clear").show();  
});  
$("input").blur(function(){  
	if($(this).val()=='')  
	{  
		$(this).parent().children(".input_clear").hide();  
	}  
});  
$(".input_clear").click(function(){  
	$(this).parent().find('input').val('');  
	$(this).hide();  
}); 