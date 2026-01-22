from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, time, random

from django.contrib import messages
from .forms import ContactForm, send_email_to_client

# ■■■■■■■■■■■■■■■■■■■■■■■■■■ EECP (eecp_about) ■■■■■■■■■■■■■■■■■■■■■■■■■■
def eecp(request):
	"""
	EECP 頁面 - 包含表單功能
	GET: 顯示頁面和表單
	POST: 處理表單提交（支援 AJAX 和普通提交）
	"""
	CAPTCHA_EXPIRY = 60  # 驗證碼有效時間（秒）

	if request.method == "POST":
		captcha_answer = request.session.get('captcha_answer')
		captcha_timestamp = request.session.get('captcha_timestamp', 0)
		
		# 檢查是否為 AJAX 請求
		is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'multipart/form-data'
		
		# 檢查驗證碼是否過期
		if time.time() - captcha_timestamp > CAPTCHA_EXPIRY:
			generate_captcha(request)
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
					"captcha_answer": request.session.get('captcha_answer'),
					'og_image': f"{settings.SITE_DOMAIN}/Public/apps/EECP/img/EECP.png"
				})
		
		form = ContactForm(request.POST, captcha_answer=captcha_answer)
		
		if form.is_valid():
			try:
				send_email_to_client(form.cleaned_data)
				
				# 清除 session 中的驗證碼
				if 'captcha_answer' in request.session:
					del request.session['captcha_answer']
				if 'captcha_timestamp' in request.session:
					del request.session['captcha_timestamp']
				
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
				generate_captcha(request)
				if is_ajax:
					return JsonResponse({
						'success': False,
						'message': '郵件寄送失敗，請稍後再試。'
					})
				else:
					messages.error(request, "郵件寄送失敗，請稍後再試。")
		else:
			# 表單驗證失敗
			generate_captcha(request)
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
				"captcha_answer": request.session.get('captcha_answer'),
				'og_image': f"{settings.SITE_DOMAIN}/Public/apps/EECP/img/EECP.png"
			})
	else:
		# GET 請求：產生新驗證碼並顯示空表單
		generate_captcha(request)
		form = ContactForm()

	return render(request, "EECP/EECP.html", {
		"form": form,
		"captcha_answer": request.session.get('captcha_answer'),
		'og_image': f"{settings.SITE_DOMAIN}/Public/apps/EECP/img/EECP.png"
	})

# ■■■■■■■■■■■■■■■■■■■■■■■■■■ EECP (eecp_contact) ■■■■■■■■■■■■■■■■■■■■■■■■■■
def generate_captcha(request):
	"""產生新的驗證碼並儲存到 session"""
	captcha_code = random.randint(1000, 9999)
	request.session['captcha_answer'] = str(captcha_code)
	request.session['captcha_timestamp'] = time.time()  # 記錄產生時間
	return captcha_code

def generate_captcha_image(request):
	"""生成干擾驗證碼圖片（PNG 格式）"""
	code = str(request.session.get('captcha_answer', '1234'))

	# 創建圖片
	width, height = 160, 60
	image = Image.new('RGB', (width, height), color=(240, 240, 240))
	draw = ImageDraw.Draw(image)

	# 嘗試載入字體（若無自訂字體會使用預設）
	try:
		font = ImageFont.truetype("arial.ttf", 36)
	except:
		font = ImageFont.load_default()

	# 繪製干擾線
	for _ in range(5):
		x1, y1 = random.randint(0, width), random.randint(0, height)
		x2, y2 = random.randint(0, width), random.randint(0, height)
		draw.line([(x1, y1), (x2, y2)], fill=(random.randint(100, 200),)*3, width=2)

	# 繪製文字（每個字元不同顏色和位置）
	char_width = width // len(code)
	for i, char in enumerate(code):
		x = char_width * i + random.randint(5, 15)
		y = random.randint(5, 15)
		color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
		draw.text((x, y), char, font=font, fill=color)

	# 添加噪點
	for _ in range(200):
		x, y = random.randint(0, width-1), random.randint(0, height-1)
		image.putpixel((x, y), (random.randint(150, 255),)*3)

	# 模糊處理
	image = image.filter(ImageFilter.GaussianBlur(radius=0.8))

	# 返回圖片
	buffer = io.BytesIO()
	image.save(buffer, 'PNG')
	buffer.seek(0)
	return HttpResponse(buffer, content_type='image/png')

# 新增：AJAX 刷新驗證碼端點
@require_GET
def refresh_captcha(request):
	"""提供前端 AJAX 刷新驗證碼"""
	captcha_code = generate_captcha(request)
	# 回傳時間戳記，讓前端知道何時產生
	return JsonResponse({
		'captcha': captcha_code,
		'timestamp': time.time()
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ EECP (submit_quiz_result) ■■■■■■■■■■■■■■■■■■■■■■■■■■
def submit_quiz_result(request):
	"""
	處理測驗結果提交（AJAX）
	"""
	if request.method != "POST":
		return JsonResponse({'success': False, 'message': '僅接受 POST 請求'}, status=405)
	
	CAPTCHA_EXPIRY = 60  # 驗證碼有效時間（秒）
	
	captcha_answer = request.session.get('captcha_answer')
	captcha_timestamp = request.session.get('captcha_timestamp', 0)
	
	# 檢查驗證碼是否過期
	if time.time() - captcha_timestamp > CAPTCHA_EXPIRY:
		generate_captcha(request)
		return JsonResponse({
			'success': False,
			'message': '驗證碼已過期，請重新輸入',
			'errors': {'captcha': '驗證碼已過期，請重新輸入'}
		})
	
	from .forms import QuizResultForm, send_quiz_result_email
	
	form = QuizResultForm(request.POST, captcha_answer=captcha_answer)
	
	if form.is_valid():
		try:
			send_quiz_result_email(form.cleaned_data)
			
			# 清除 session 中的驗證碼
			if 'captcha_answer' in request.session:
				del request.session['captcha_answer']
			if 'captcha_timestamp' in request.session:
				del request.session['captcha_timestamp']
			
			return JsonResponse({
				'success': True,
				'message': '您的測驗結果已成功送出，感謝您的聯繫！'
			})
		except Exception as e:
			import logging
			logging.exception("send_quiz_result_email failed")
			generate_captcha(request)
			return JsonResponse({
				'success': False,
				'message': '郵件寄送失敗，請稍後再試。'
			})
	else:
		# 表單驗證失敗
		generate_captcha(request)
		errors = {}
		for field, error_list in form.errors.items():
			errors[field] = error_list[0] if error_list else '此欄位有誤'
		
		return JsonResponse({
			'success': False,
			'message': '表單驗證失敗，請檢查您的輸入',
			'errors': errors
		})
