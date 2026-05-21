# 供 Breast_Care_Center 等 app 使用的 rate limit / captcha 裝飾器
from functools import wraps
from django.shortcuts import redirect


def ratelimit_captcha(max_requests=10, window=60):
	"""限制驗證碼刷新頻率：window 秒內最多 max_requests 次（以 IP + session 計）"""
	def decorator(view_func):
		@wraps(view_func)
		def _wrapped_view(request, *args, **kwargs):
			from django.core.cache import cache
			import time
			key = f"captcha_refresh:{request.META.get('REMOTE_ADDR', '')}"
			data = cache.get(key) or {'count': 0, 'start': time.time()}
			now = time.time()
			if now - data['start'] > window:
				data = {'count': 0, 'start': now}
			data['count'] += 1
			cache.set(key, data, timeout=window)
			if data['count'] > max_requests:
				from django.http import JsonResponse
				return JsonResponse({'success': False, 'message': '刷新次數過多，請稍後再試'}, status=429)
			return view_func(request, *args, **kwargs)
		return _wrapped_view
	return decorator


def ratelimit_form_submit(max_requests=5, window=300, redirect_url='breast_send_mail'):
	"""限制表單提交頻率"""
	def decorator(view_func):
		@wraps(view_func)
		def _wrapped_view(request, *args, **kwargs):
			if request.method != 'POST':
				return view_func(request, *args, **kwargs)
				
			from django.core.cache import cache
			import time
			key = f"form_submit:{request.META.get('REMOTE_ADDR', '')}"
			data = cache.get(key) or {'count': 0, 'start': time.time()}
			now = time.time()
			if now - data['start'] > window:
				data = {'count': 0, 'start': now}
			data['count'] += 1
			cache.set(key, data, timeout=window)
			if data['count'] > max_requests:
				is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or (request.content_type and request.content_type.startswith('multipart/form-data'))
				if is_ajax:
					from django.http import JsonResponse
					return JsonResponse({
						'success': False,
						'message': '您送出表單的頻率過高，請稍後再試。'
					}, status=429)
				from django.contrib import messages
				messages.error(request, '您送出表單的頻率過高，請稍後再試。')
				return redirect(redirect_url)
			return view_func(request, *args, **kwargs)
		return _wrapped_view
	return decorator


def captcha_failure_limit(max_failures=5, lockout_time=300, redirect_url='breast_send_mail', captcha_field='captcha'):
	"""驗證碼錯誤達 max_failures 次後鎖定 lockout_time 秒"""
	def decorator(view_func):
		@wraps(view_func)
		def _wrapped_view(request, *args, **kwargs):
			if request.method != 'POST':
				return view_func(request, *args, **kwargs)
			from django.core.cache import cache
			import time
			key = f"captcha_fail:{request.META.get('REMOTE_ADDR', '')}"
			data = cache.get(key) or {'count': 0, 'locked_until': 0}
			now = time.time()
			if now < data['locked_until']:
				is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or (request.content_type and request.content_type.startswith('multipart/form-data'))
				if is_ajax:
					from django.http import JsonResponse
					return JsonResponse({
						'success': False,
						'message': '驗證碼錯誤次數過多，已暫時鎖定，請稍後再試。'
					}, status=403)
				return redirect(redirect_url)
			# 只在不成功時增加計數（在 view 內表單 invalid 時由 view 自己呼叫 cache 增加）
			# 此裝飾器僅做「鎖定期間內直接 redirect」
			return view_func(request, *args, **kwargs)
		return _wrapped_view
	return decorator
