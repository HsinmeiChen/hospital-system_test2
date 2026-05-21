# 只是開發階段用來輔助驗證的工具。正式上線或平常運行時，它是不會執行的，是一個靜態的程式碼檔案，安靜地躺在資料夾裡，不佔用任何 CPU 運算資源或記憶體，也不會影響網頁載入速度。未來如果網站突然發生表單送不出或驗證碼有問題時，開發人員只要下一行指令就能立刻找出問題點，是一個人工測試的後備防禦機制。

from django.test import TestCase, Client
from django.urls import reverse
import time

class EECPFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.booking_url = reverse('eecp')
        self.quiz_url = '/EECP/api/submit-quiz-result/'

    def test_booking_form_valid_captcha(self):
        """測試預約表單：正確的驗證碼（2分鐘內）應成功"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time()
        session.save()

        post_data = {
            'name': '測試員',
            'email': 'test@example.com',
            'phone': '0912345678',
            'appointment_date': '2026-12-31',
            'message': '測試內容',
            'captcha': '12345'
        }
        # 使用 AJAX 標頭提交
        response = self.client.post(
            self.booking_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_booking_form_invalid_captcha(self):
        """測試預約表單：錯誤的驗證碼（2分鐘內）應回傳驗證碼錯誤訊息"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time()
        session.save()

        post_data = {
            'name': '測試員',
            'email': 'test@example.com',
            'phone': '0912345678',
            'appointment_date': '2026-12-31',
            'message': '測試內容',
            'captcha': '54321' # 錯誤的驗證碼
        }
        response = self.client.post(
            self.booking_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors']['captcha'], '驗證碼錯誤，請重新輸入')

    def test_booking_form_expired_captcha(self):
        """測試預約表單：驗證碼過期（即使輸入正確）應回傳已過期訊息"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time() - 130 # 超過 120 秒
        session.save()

        post_data = {
            'name': '測試員',
            'email': 'test@example.com',
            'phone': '0912345678',
            'appointment_date': '2026-12-31',
            'message': '測試內容',
            'captcha': '12345' # 雖然正確，但已過期
        }
        response = self.client.post(
            self.booking_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors']['captcha'], '驗證碼已過期，請重新輸入')

    def test_booking_form_expired_incorrect_captcha(self):
        """測試預約表單：驗證碼過期且輸入錯誤，應回傳已過期訊息"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time() - 130 # 超過 120 秒
        session.save()

        post_data = {
            'name': '測試員',
            'email': 'test@example.com',
            'phone': '0912345678',
            'appointment_date': '2026-12-31',
            'message': '測試內容',
            'captcha': '99999' # 錯誤且過期
        }
        response = self.client.post(
            self.booking_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors']['captcha'], '驗證碼已過期，請重新輸入')

    def test_quiz_form_valid_captcha(self):
        """測試測驗結果表單：正確驗證碼（2分鐘內）應成功"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time()
        session.save()

        post_data = {
            'name': '測驗者',
            'email': 'quiz@example.com',
            'phone': '0912345678',
            'result': '低風險 - 健康狀況良好',
            'score': '5',
            'quiz_captcha': '12345'
        }
        response = self.client.post(
            self.quiz_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_quiz_form_expired_captcha(self):
        """測試測驗結果表單：驗證碼過期應回傳過期訊息"""
        session = self.client.session
        session['common_captcha_code'] = '12345'
        session['common_captcha_timestamp'] = time.time() - 130 # 超過 120 秒
        session.save()

        post_data = {
            'name': '測驗者',
            'email': 'quiz@example.com',
            'phone': '0912345678',
            'result': '低風險',
            'score': '5',
            'quiz_captcha': '12345'
        }
        response = self.client.post(
            self.quiz_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['errors']['quiz_captcha'], '驗證碼已過期，請重新輸入')
