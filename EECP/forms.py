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
	name = forms.CharField(
		label="姓名",
		max_length=100,
		widget=forms.TextInput(attrs={
			'placeholder': '請輸入您的姓名'
		})
	)
	email = forms.EmailField(
		label="電子郵件",
		widget=forms.EmailInput(attrs={
			'placeholder': '請輸入您的 Email'
		})
	)
	phone = forms.CharField(
		label="聯絡電話",
		max_length=16,  # 15 碼數字 + 1 個 + 號
		# required=False,
		validators=[validate_phone_number],
		widget=forms.TextInput(attrs={
			'pattern': r'^\+?\d{8,15}$',
			'title': '請輸入 8~15 碼數字，國際格式可加 + 號於開頭',
			'maxlength': '16',
			'placeholder': '請輸入您的聯絡電話'
		})
	)
	appointment_date = forms.DateField(
		label="希望預約時間",
		widget=forms.DateInput(attrs={
			'type': 'date',
			'placeholder': '請選擇日期'
		})
	)
	message = forms.CharField(
		label="其他需求或問題", widget=forms.Textarea(attrs={
			'placeholder': '請告訴我們您的需求...',
			'rows': 4
		})
	)

	# 新增驗證碼欄位
	captcha = forms.CharField(
		label="驗證碼",
		max_length=4,
		widget=forms.TextInput(attrs={
			'placeholder': '請輸入驗證碼數字',
			'autocomplete': 'off'
		})
	)

	def __init__(self, *args, **kwargs):
		self.captcha_answer = kwargs.pop('captcha_answer', None)
		super().__init__(*args, **kwargs)

	def clean_captcha(self):
		user_input = self.cleaned_data.get('captcha')
		if str(user_input) != str(self.captcha_answer):
			raise ValidationError("驗證碼錯誤，請重新輸入")
		return user_input

def send_email_to_client(cleaned_data):
	"""
	cleaned_data: ContactForm.cleaned_data
	寄信到內部收件者，使用 HTML template 格式
    """    
	subject = f"[長安醫院-EECP 體外反搏治療中心 - 預約諮詢] {cleaned_data['name']}"

	# 用 Django template 渲染 HTML
	html_body = render_to_string('EECP/eecp-email-content.html', {
		'name': cleaned_data['name'],
		'email': cleaned_data['email'],
		'phone': cleaned_data.get('phone', ''),
		'appointment_date': cleaned_data['appointment_date'],
		'message': cleaned_data['message'],
	})

	email = EmailMessage(
		subject=subject,
		body=html_body,
		from_email=settings.DEFAULT_FROM_EMAIL,
		to=[
			'ha01633@everanhospital.com.tw'
		],
		reply_to=[cleaned_data['email']],
	)
	email.content_subtype = 'html' # 設定郵件內容為 HTML 格式 (避免 html 標籤被當成純文字顯示)
	email.send(fail_silently=False)


# 測驗結果表單
class QuizResultForm(forms.Form):
	name = forms.CharField(
		label="姓名",
		max_length=100,
		widget=forms.TextInput(attrs={
			'placeholder': '請輸入您的姓名'
		})
	)
	email = forms.EmailField(
		label="電子郵件",
		widget=forms.EmailInput(attrs={
			'placeholder': '請輸入您的 Email'
		})
	)
	phone = forms.CharField(
		label="聯絡電話",
		max_length=16,
		validators=[validate_phone_number],
		widget=forms.TextInput(attrs={
			'pattern': r'^\+?\d{8,15}$',
			'title': '請輸入 8~15 碼數字，國際格式可加 + 號於開頭',
			'maxlength': '16',
			'placeholder': '請輸入您的聯絡電話'
		})
	)
	result = forms.CharField(
		label="評估結果",
		max_length=200
	)
	score = forms.IntegerField(
		label="評估分數"
	)
	
	# 驗證碼欄位（使用不同名稱避免與預約表單衝突）
	quiz_captcha = forms.CharField(
		label="",
		max_length=4,
		widget=forms.TextInput(attrs={
			'placeholder': '請輸入驗證碼數字',
			'autocomplete': 'off',
			'id': 'quizCaptcha'  # 明確指定 id
		})
	)

	def __init__(self, *args, **kwargs):
		self.captcha_answer = kwargs.pop('captcha_answer', None)
		super().__init__(*args, **kwargs)

	def clean_quiz_captcha(self):
		user_input = self.cleaned_data.get('quiz_captcha')
		if str(user_input) != str(self.captcha_answer):
			raise ValidationError("驗證碼錯誤，請重新輸入")
		return user_input


def send_quiz_result_email(cleaned_data):
	"""
	發送測驗結果郵件
	"""
	subject = f"[長安醫院-EECP 體外反搏治療中心 - 測驗結果諮詢] {cleaned_data['name']}"

	# 用 Django template 渲染 HTML
	html_body = render_to_string('EECP/eecp-quiz-result-email.html', {
		'name': cleaned_data['name'],
		'email': cleaned_data['email'],
		'phone': cleaned_data.get('phone', ''),
		'result': cleaned_data['result'],
		'score': cleaned_data['score'],
	})

	email = EmailMessage(
		subject=subject,
		body=html_body,
		from_email=settings.DEFAULT_FROM_EMAIL,
		to=[
			'ha01633@everanhospital.com.tw'
		],
		reply_to=[cleaned_data['email']],
	)
	email.content_subtype = 'html'
	email.send(fail_silently=False)
