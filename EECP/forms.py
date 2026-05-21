from django import forms
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from Pomelo_test.forms import FeedbackBaseForm, validate_phone_number

class ContactForm(FeedbackBaseForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# 保留 EECP 專屬的 Placeholder 客製化
		self.fields['name'].widget.attrs.update({'placeholder': '請輸入您的姓名'})
		self.fields['email'].widget.attrs.update({'placeholder': '請輸入您的 Email'})
		self.fields['phone'].widget.attrs.update({
			'pattern': r'^\+?\d{8,15}$',
			'title': '請輸入 8~15 碼數字，國際格式可加 + 號於開頭',
			'maxlength': '16',
			'placeholder': '請輸入您的聯絡電話'
		})
		self.fields['message'].label = '其他需求或問題'
		self.fields['message'].widget.attrs.update({
			'placeholder': '請告訴我們您的需求...',
			'rows': 4
		})
		self.fields['captcha'].widget.attrs.update({
			'placeholder': '請輸入5位數字驗證碼',
			'autocomplete': 'off',
			'maxlength': '5',
			'pattern': '[0-9]{5}',
			'title': '請輸入5位數字驗證碼'
		})
		
		# 限制希望預約時間不能選擇過去的日期
		from datetime import date
		self.fields['appointment_date'].widget.attrs.update({
			'min': date.today().isoformat()
		})

	appointment_date = forms.DateField(
		label="希望預約時間",
		widget=forms.DateInput(attrs={
			'type': 'date',
			'placeholder': '請選擇日期'
		})
	)

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
		to=settings.CONTACT_EMAIL_RECIPIENTS_EECP,
		reply_to=[cleaned_data['email']],
	)
	email.content_subtype = 'html' # 設定郵件內容為 HTML 格式 (避免 html 標籤被當成純文字顯示)
	email.send(fail_silently=False)


# 測驗結果表單 (無 message 欄位，故不繼承 FeedbackBaseForm，但共用 validate_phone_number)
class QuizResultForm(forms.Form):
	name = forms.CharField(
		label="姓名",
		max_length=100,
		error_messages={'required': '請填寫您的姓名'},
		widget=forms.TextInput(attrs={
			'placeholder': '請輸入您的姓名'
		})
	)
	email = forms.EmailField(
		label="電子郵件",
		error_messages={'invalid': '請輸入正確的 E-mail 格式', 'required': '請填寫您的 Email'},
		widget=forms.EmailInput(attrs={
			'placeholder': '請輸入您的 Email'
		})
	)
	phone = forms.CharField(
		label="聯絡電話",
		max_length=16,
		validators=[validate_phone_number],
		error_messages={'required': '請填寫您的聯絡電話'},
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
		max_length=5,
		min_length=5,
		widget=forms.TextInput(attrs={
			'placeholder': '請輸入5位數字驗證碼',
			'autocomplete': 'off',
			'maxlength': '5',
			'pattern': '[0-9]{5}',
			'title': '請輸入5位數字驗證碼',
			'id': 'quizCaptcha'  # 明確指定 id
		})
	)

	def __init__(self, *args, **kwargs):
		self.captcha_answer = kwargs.pop('captcha_answer', None)
		super().__init__(*args, **kwargs)

	def clean_quiz_captcha(self):
		user_input = self.cleaned_data.get('quiz_captcha', '').strip()
		if not self.captcha_answer or user_input != str(self.captcha_answer):
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
		to=settings.CONTACT_EMAIL_RECIPIENTS_EECP,
		reply_to=[cleaned_data['email']],
	)
	email.content_subtype = 'html'
	email.send(fail_silently=False)
