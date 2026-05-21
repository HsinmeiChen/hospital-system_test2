from django import forms
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

class FeedbackBaseForm(forms.Form):
    """通用的基底表單，包含所有意見反映、聯絡我們都會用到的基本欄位"""
    name = forms.CharField(max_length=50, label='姓名', error_messages={'required': '請填寫您的姓名'}, widget=forms.TextInput(attrs={'class': 'form-control border-coco rounded-0 input2'}))
    phone = forms.CharField(max_length=20, required=False, label='聯絡電話', error_messages={'required': '請填寫您的聯絡電話'}, validators=[validate_phone_number], widget=forms.TextInput(attrs={'class': 'form-control border-coco rounded-0 input2'}))
    email = forms.EmailField(required=False, label='Email', error_messages={'invalid': '請輸入正確的 E-mail 格式', 'required': '請填寫您的 Email'}, widget=forms.EmailInput(attrs={'class': 'form-control border-coco rounded-0 input2'}))
    message = forms.CharField(max_length=500, label='反應內容或事件經過', error_messages={'required': '請填寫您的內容'}, widget=forms.Textarea(attrs={'class': 'form-control border-coco rounded-0 textarea input2', 'rows': '6', 'id': 'msgus'}))
    captcha = forms.CharField(max_length=5, label='驗證碼', error_messages={'required': '請填寫驗證碼'}, widget=forms.TextInput(attrs={'class': 'form-control border-coco rounded-0 input2'}))

    def __init__(self, *args, **kwargs):
        self.captcha_answer = kwargs.pop('captcha_answer', None)
        super().__init__(*args, **kwargs)

    def clean_captcha(self):
        user_input = self.cleaned_data.get('captcha', '').strip()
        # 如果有傳入 captcha_answer，就直接在表單做驗證碼比對
        if self.captcha_answer is not None:
            if not self.captcha_answer or str(user_input).lower() != str(self.captcha_answer).lower():
                raise ValidationError("驗證碼錯誤，請重新輸入")
        return user_input

class ContactUsForm(FeedbackBaseForm):
    """主站意見反映專用表單，擴充了分類、日期、時間與地點"""
    CATEGORY_CHOICES = [
        ('讚美', '讚美'),
        ('申訴', '申訴'),
        ('建議', '建議'),
        ('諮詢', '諮詢'),
    ]
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, label='反應事件類別', widget=forms.RadioSelect)
    incident_date = forms.DateField(required=False, label='事件發生日期', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control border-coco rounded-0 input2'}))
    incident_time = forms.TimeField(required=False, label='事件發生時間', widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control border-coco rounded-0 input2'}))
    place = forms.CharField(max_length=100, required=False, label='發生地點', widget=forms.TextInput(attrs={'class': 'form-control border-coco rounded-0 input2'}))
