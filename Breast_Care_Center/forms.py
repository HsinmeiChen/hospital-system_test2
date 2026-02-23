from django import forms
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
import re
from django.core.exceptions import ValidationError


def validate_phone_number(value):
	"""
	電話號碼驗證：
	- 允許數字和 + 號（國際格式）
	- + 號只能出現在開頭
	- 長度限制：8 到 15 碼（不含 + 號）
	"""
	if not value:
		return
	if not re.match(r'^\+?\d+$', value):
		raise ValidationError("電話號碼僅可包含數字，+ 號只能在開頭。")
	# 計算純數字長度（排除 +）
	digits = re.sub(r'\D', '', value)
	if len(digits) < 8 or len(digits) > 15:
		raise ValidationError("電話號碼需為 8 到 15 碼。")

class ContactForm(forms.Form):
	name = forms.CharField(label="姓名", max_length=100)
	email = forms.EmailField(label="信箱")
	phone = forms.CharField(
		label="聯絡電話",
		max_length=16,  # 15 碼數字 + 1 個 + 號
		# required=False,
		validators=[validate_phone_number],
		widget=forms.TextInput(attrs={
			'pattern': r'^\+?\d{8,15}$',
			'title': '請輸入 8~15 碼數字，國際格式可加 + 號於開頭',
			'maxlength': '16',
			'placeholder': '例：0912345678 或 +886912345678'
		})
	)
	subject = forms.CharField(label="主旨", max_length=255)
	message = forms.CharField(label="內容", widget=forms.Textarea)

	# 新增驗證碼欄位
	captcha = forms.CharField(
		label="驗證碼",
		max_length=5,
		min_length=5,
		widget=forms.TextInput(attrs={
			'placeholder': '請輸入5位數字驗證碼',
			'autocomplete': 'off',
			'maxlength': '5',
			'pattern': '[0-9]{5}',
			'title': '請輸入5位數字驗證碼'
		})
	)

	def __init__(self, *args, **kwargs):
		self.captcha_answer = kwargs.pop('captcha_answer', None)
		super().__init__(*args, **kwargs)

	def clean_captcha(self):
		user_input = self.cleaned_data.get('captcha', '').strip()  # 數字不需轉大小寫
		if user_input != str(self.captcha_answer):
			raise ValidationError("驗證碼錯誤，請重新輸入")
		return user_input

def send_email_to_client(cleaned_data):
	"""
	cleaned_data: ContactForm.cleaned_data
	寄信到內部收件者，使用 HTML template 格式
    """    
	subject = f"【長安醫院-全方位乳房中心】客服信件 {cleaned_data['subject']}"

	# 用 Django template 渲染 HTML
	html_body = render_to_string('Breast_Care_Center/breast-email-content.html', {
		'name': cleaned_data['name'],
		'email': cleaned_data['email'],
		'phone': cleaned_data.get('phone', ''),
		'subject': cleaned_data['subject'],
		'message': cleaned_data['message'],
	})

	email = EmailMessage(
		subject=subject,
		body=html_body,
		from_email=settings.DEFAULT_FROM_EMAIL,
		to=settings.CONTACT_EMAIL_RECIPIENTS_BREAST,
		reply_to=[cleaned_data['email']],
	)
	email.content_subtype = 'html' # 設定郵件內容為 HTML 格式 (避免 html 標籤被當成純文字顯示)
	email.send(fail_silently=False)
