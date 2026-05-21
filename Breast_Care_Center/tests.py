# 只是開發階段用來輔助驗證的工具。正式上線或平常運行時，它是不會執行的，是一個靜態的程式碼檔案，安靜地躺在資料夾裡，不佔用任何 CPU 運算資源或記憶體，也不會影響網頁載入速度。未來如果網站突然發生表單送不出或驗證碼有問題時，開發人員只要下一行指令就能立刻找出問題點，是一個人工測試的後備防禦機制。

from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
import time

class BreastCareCenterFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.breast_url = reverse('breast_send_mail')
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_breast_contact_form_valid_captcha(self):
        """測試乳房中心表單：正確驗證碼應成功"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time()
        session.save()

        post_data = {
            'name': '乳房中心測試員',
            'email': 'breast@example.com',
            'phone': '0912345678',
            'subject': '一般預約諮詢',
            'message': '測試乳房中心表單內容',
            'captcha': '12345'
        }
        response = self.client.post(
            self.breast_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_breast_contact_form_invalid_captcha(self):
        """測試乳房中心表單：錯誤驗證碼應顯示錯誤提示"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time()
        session.save()

        post_data = {
            'name': '乳房中心測試員',
            'email': 'breast@example.com',
            'phone': '0912345678',
            'subject': '一般預約諮詢',
            'message': '測試乳房中心表單內容',
            'captcha': '54321'
        }
        response = self.client.post(
            self.breast_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors']['captcha'], '驗證碼錯誤，請重新輸入')

    def test_breast_contact_form_expired_captcha(self):
        """測試乳房中心表單：驗證碼過期（即使輸入正確）應顯示過期提示"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time() - 130
        session.save()

        post_data = {
            'name': '乳房中心測試員',
            'email': 'breast@example.com',
            'phone': '0912345678',
            'subject': '一般預約諮詢',
            'message': '測試乳房中心表單內容',
            'captcha': '12345'
        }
        response = self.client.post(
            self.breast_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors']['captcha'], '驗證碼已過期，請重新輸入')
