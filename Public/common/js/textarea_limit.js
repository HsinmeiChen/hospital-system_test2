var maxLength = 150;
$('textarea').keyup(function() {
	var textlen = maxLength - $(this).val().length;
	$('#rchars').text(textlen);
});