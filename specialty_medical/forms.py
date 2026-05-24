from django import forms
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from Pomelo_test.forms import FeedbackBaseForm

class ContactForm(FeedbackBaseForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['name'].widget.attrs.update({'placeholder': ''})
		self.fields['email'].widget.attrs.update({'placeholder': ''})
		self.fields['phone'].widget.attrs.update({
			'pattern': r'^\+?\d{8,15}$',
			'title': '請輸入 8~15 碼數字，國際格式可加 + 號於開頭',
			'maxlength': '16',
			'placeholder': '例：0912345678 或 +886912345678'
		})
		self.fields['message'].label = "內容"
		self.fields['captcha'].widget.attrs.update({
			'placeholder': '請輸入5位數字驗證碼',
			'autocomplete': 'off',
			'maxlength': '5',
			'pattern': '[0-9]{5}',
			'title': '請輸入5位數字驗證碼'
		})

	subject = forms.CharField(label="主旨", max_length=255)

def send_email_to_client(cleaned_data):
	"""
	cleaned_data: ContactForm.cleaned_data
	寄信到內部收件者，使用 HTML template 格式
	"""    
	subject = f"【長安醫院-骨科微創手術中心】客服信件 {cleaned_data['subject']}"

	# 用 Django template 渲染 HTML (沿用 Breast_Care_Center 的樣板或自行定義，這裡先直接組合 HTML 字串或建立專屬的 html)
	html_body = f"""
	<html>
		<body>
			<h2>長安醫院-骨科微創手術中心 聯絡表單通知</h2>
			<p><strong>姓名：</strong> {cleaned_data.get('name')}</p>
			<p><strong>信箱：</strong> {cleaned_data.get('email')}</p>
			<p><strong>電話：</strong> {cleaned_data.get('phone', '未提供')}</p>
			<p><strong>主旨：</strong> {cleaned_data.get('subject')}</p>
			<hr>
			<p><strong>內容：</strong></p>
			<p>{cleaned_data.get('message').replace(chr(10), '<br>')}</p>
		</body>
	</html>
	"""

	email = EmailMessage(
		subject=subject,
		body=html_body,
		from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@everanhospital.com.tw'),
		to=['ha01633@everanhospital.com.tw'],
		reply_to=[cleaned_data['email']],
	)
	email.content_subtype = 'html' # 設定郵件內容為 HTML 格式 (避免 html 標籤被當成純文字顯示)
	email.send(fail_silently=False)
