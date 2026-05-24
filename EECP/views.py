from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, time, random

from django.contrib import messages
from Pomelo_test.utils import generate_captcha_image_bytes
from .forms import ContactForm, send_email_to_client

# ■■■■■■■■■■■■■■■■■■■■■■■■■■ EECP (eecp_about) ■■■■■■■■■■■■■■■■■■■■■■■■■■
def eecp(request):
	"""
	EECP 頁面 - 包含表單功能
	GET: 顯示頁面和表單
	POST: 處理表單提交（支援 AJAX 和普通提交）
	"""
	CAPTCHA_EXPIRY = 120  # 驗證碼有效時間（秒，2分鐘）

	if request.method == "POST":
		captcha_answer = request.session.get('common_captcha_code')
		captcha_timestamp = request.session.get('common_captcha_timestamp', 0)
		
		# 檢查是否為 AJAX 請求
		is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or (request.content_type and request.content_type.startswith('multipart/form-data'))
		
		# 檢查驗證碼是否過期
		if time.time() - captcha_timestamp > CAPTCHA_EXPIRY:
			if is_ajax:
				return JsonResponse({
					'success': False,
					'message': '驗證碼已過期，請重新輸入',
					'errors': {'captcha': '驗證碼已過期，請重新輸入'}
				})
			else:
				messages.error(request, "驗證碼已過期，請重新整理後再試")
				form = ContactForm()
				return render(request, "EECP/EECP.html", {
					"form": form,
				})
		
		form = ContactForm(request.POST, captcha_answer=captcha_answer)
		
		if form.is_valid():
			try:
				send_email_to_client(form.cleaned_data)
				
				# 清除 session 中的驗證碼
				if 'common_captcha_code' in request.session:
					del request.session['common_captcha_code']
				if 'common_captcha_timestamp' in request.session:
					del request.session['common_captcha_timestamp']
				
				if is_ajax:
					return JsonResponse({
						'success': True,
						'message': '您的訊息已成功送出，感謝您的聯繫！'
					})
				else:
					messages.success(request, "您的訊息已成功送出，感謝您的聯繫！")
					return redirect('eecp')
			except Exception as e:
				import logging
				logging.exception("send_mail failed in eecp view")
				if is_ajax:
					return JsonResponse({
						'success': False,
						'message': '郵件寄送失敗，請稍後再試。'
					})
				else:
					messages.error(request, "郵件寄送失敗，請稍後再試。")
		else:
			# 表單驗證失敗
			if is_ajax:
				errors = {}
				for field, error_list in form.errors.items():
					errors[field] = error_list[0] if error_list else '此欄位有誤'
				
				return JsonResponse({
					'success': False,
					'message': '表單驗證失敗，請檢查您的輸入',
					'errors': errors
				})
		
		if not is_ajax:
			return render(request, "EECP/EECP.html", {
				"form": form,
			})
	else:
		form = ContactForm()

	return render(request, "EECP/EECP.html", {
		"form": form,
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ EECP (submit_quiz_result) ■■■■■■■■■■■■■■■■■■■■■■■■■■
def submit_quiz_result(request):
	"""
	處理測驗結果提交（AJAX）
	"""
	if request.method != "POST":
		return JsonResponse({'success': False, 'message': '僅接受 POST 請求'}, status=405)
	
	CAPTCHA_EXPIRY = 120  # 驗證碼有效時間（秒，2分鐘）
	
	captcha_answer = request.session.get('common_captcha_code')
	captcha_timestamp = request.session.get('common_captcha_timestamp', 0)
	
	# 檢查驗證碼是否過期
	if time.time() - captcha_timestamp > CAPTCHA_EXPIRY:
		return JsonResponse({
			'success': False,
			'message': '驗證碼已過期，請重新輸入',
			'errors': {'quiz_captcha': '驗證碼已過期，請重新輸入'}
		})
	
	from .forms import QuizResultForm, send_quiz_result_email
	
	form = QuizResultForm(request.POST, captcha_answer=captcha_answer)
	
	if form.is_valid():
		try:
			send_quiz_result_email(form.cleaned_data)
			
			# 清除 session 中的驗證碼
			if 'common_captcha_code' in request.session:
				del request.session['common_captcha_code']
			if 'common_captcha_timestamp' in request.session:
				del request.session['common_captcha_timestamp']
			
			return JsonResponse({
				'success': True,
				'message': '您的測驗結果已成功送出，感謝您的聯繫！'
			})
		except Exception as e:
			import logging
			logging.exception("send_quiz_result_email failed")
			return JsonResponse({
				'success': False,
				'message': '郵件寄送失敗，請稍後再試。'
			})
	else:
		# 表單驗證失敗
		errors = {}
		for field, error_list in form.errors.items():
			errors[field] = error_list[0] if error_list else '此欄位有誤'
		
		return JsonResponse({
			'success': False,
			'message': '表單驗證失敗，請檢查您的輸入',
			'errors': errors
		})
