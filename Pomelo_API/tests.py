# 只是開發階段用來輔助驗證的工具。正式上線或平常運行時，它是不會執行的，是一個靜態的程式碼檔案，安靜地躺在資料夾裡，不佔用任何 CPU 運算資源或記憶體，也不會影響網頁載入速度。未來如果網站突然發生表單送不出或驗證碼有問題時，開發人員只要下一行指令就能立刻找出問題點，是一個人工測試的後備防禦機制。


from django.test import TestCase, Client, override_settings
from django.core.cache import cache
import time

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ContactUsFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.contact_url = '/A004_contact_us/'
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_contact_us_form_get(self):
        """測試意見反映表單 GET 請求：應回傳正常網頁"""
        response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '意見反映')

    def test_contact_us_form_valid_captcha_ajax(self):
        """測試意見反映表單 AJAX 提交：正確驗證碼應成功"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time()
        session.save()

        post_data = {
            'category': '建議',
            'name': '測試者',
            'phone': '0912345678',
            'email': 'test@example.com',
            'message': '這是一條測試的意見反映內容，內容長度足夠。',
            'captcha': '12345'
        }
        response = self.client.post(
            self.contact_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], '您的意見已成功送出，我們會盡快處理！')

    def test_contact_us_form_invalid_captcha_ajax(self):
        """測試意見反映表單 AJAX 提交：錯誤驗證碼應回傳紅字提示錯誤"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time()
        session.save()

        post_data = {
            'category': '建議',
            'name': '測試者',
            'phone': '0912345678',
            'email': 'test@example.com',
            'message': '這是一條測試的意見反映內容，內容長度足夠。',
            'captcha': '54321'  # 錯誤的驗證碼
        }
        response = self.client.post(
            self.contact_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors']['captcha'], '驗證碼錯誤，請重新輸入')

    def test_contact_us_form_expired_captcha_ajax(self):
        """測試意見反映表單 AJAX 提交：驗證碼已過期 (超過 2 分鐘) 應回傳過期提示"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time() - 130  # 超過 120 秒
        session.save()

        post_data = {
            'category': '建議',
            'name': '測試者',
            'phone': '0912345678',
            'email': 'test@example.com',
            'message': '這是一條測試的意見反映內容，內容長度足夠。',
            'captcha': '12345'  # 驗證碼正確但已過期
        }
        response = self.client.post(
            self.contact_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors']['captcha'], '驗證碼已過期，請重新輸入')

    def test_contact_us_form_lockout_ajax(self):
        """測試意見反映表單 AJAX 提交：驗證碼錯誤次數過多時應觸發 lockout 限制並回傳 403"""
        # 模擬已經有 5 次驗證碼錯誤
        from django.core.cache import cache
        key = f"captcha_fail:{self.client.session.session_key or '127.0.0.1'}"
        # 因為測試 Client 沒有真實的 REMOTE_ADDR，如果 decorator 抓 IP，我們會以空字串或 testserver IP 為主
        # decorators.py 使用 request.META.get('REMOTE_ADDR', '')
        # 測試環境中，Client 發起請求的 REMOTE_ADDR 預設是 '127.0.0.1'
        key = "captcha_fail:127.0.0.1"
        cache.set(key, {'count': 5, 'locked_until': time.time() + 300}, timeout=300)

        post_data = {
            'category': '建議',
            'name': '測試者',
            'phone': '0912345678',
            'email': 'test@example.com',
            'message': '這是一條測試的意見反映內容，內容長度足夠。',
            'captcha': '12345'
        }
        response = self.client.post(
            self.contact_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], '驗證碼錯誤次數過多，已暫時鎖定，請稍後再試。')
