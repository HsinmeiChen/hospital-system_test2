# 供 Breast_Care_Center 等 app 使用：為檔名附加 hash（用於衛教等 txt 檔）
import io
import os
import random
import zlib
import traceback

try:
	from PIL import Image, ImageDraw, ImageFont
except ImportError:
	Image = ImageDraw = ImageFont = None

# --- 安全檔案鎖匯入 ---
try:
	from filelock import FileLock
except ImportError:
	FileLock = None

# --- PDF 轉圖工具匯入 ---
# PyMuPDF - 用於將 PDF 轉換成圖片，不需要外部 Poppler 依賴
try:
	import fitz  
except ImportError:
	fitz = None

# --- Django 設定匯入 ---
from django.conf import settings


def generate_captcha_image_bytes(code):
	"""
	產生「第一種風格」驗證碼圖片：網格背景（淺紫/粉）、多色小點、多色波浪干擾線、五位數字。
	code: 驗證碼字串（如 "78855"）
	回傳: PNG 圖片 bytes，供 HttpResponse(content, content_type='image/png') 使用。
	"""
	if Image is None:
		raise RuntimeError("PIL is required for captcha image generation")
	code = str(code)
	width, height = 160, 60
	# 淺紫/粉背景（第一種風格）
	bg = (random.randint(232, 242), random.randint(224, 236), random.randint(238, 248))
	image = Image.new('RGB', (width, height), color=bg)
	draw = ImageDraw.Draw(image)

	# 網格背景（方格紙感）
	grid_size = 6
	grid_color = (max(0, bg[0] - 18), max(0, bg[1] - 20), max(0, bg[2] - 15))
	for x in range(0, width, grid_size):
		draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
	for y in range(0, height, grid_size):
		draw.line([(0, y), (width, y)], fill=grid_color, width=1)

	try:
		font = ImageFont.truetype("arial.ttf", 36)
	except Exception:
		font = ImageFont.load_default()

	# 多色波浪/鋸齒干擾線（棕、深綠、紫、紅褐等）
	line_colors = [
		(101, 80, 60), (60, 90, 65), (120, 100, 145), (130, 75, 70),
		(85, 95, 75), (110, 85, 120), (90, 70, 65),
	]
	for _ in range(7):
		points = []
		x, y = random.randint(0, width), random.randint(0, height)
		for _ in range(4 + random.randint(0, 2)):
			x = max(0, min(width, x + random.randint(-25, 25)))
			y = max(0, min(height, y + random.randint(-12, 12)))
			points.append((x, y))
		if len(points) >= 2:
			draw.line(points, fill=random.choice(line_colors), width=random.randint(1, 2))

	# 數字：每個字元不同深色、隨機歪斜（旋轉 -18～18 度）增加干擾
	char_width = width // len(code)
	digit_colors = [(50, 50, 55), (45, 75, 50), (75, 65, 45), (100, 55, 50), (60, 70, 90)]
	for i, char in enumerate(code):
		color = digit_colors[i % len(digit_colors)]
		# 在透明小圖上畫單一數字
		char_img = Image.new('RGBA', (40, 44), (255, 255, 255, 0))
		char_draw = ImageDraw.Draw(char_img)
		char_draw.text((6, 2), char, font=font, fill=color)
		# 隨機旋轉造成歪斜
		angle = random.randint(-18, 18)
		char_img = char_img.rotate(angle, expand=False, resample=Image.BICUBIC, fillcolor=(255, 255, 255, 0))
		# 貼到主圖（旋轉後可能超出，取可貼範圍）
		px = char_width * i + random.randint(5, 10)
		py = random.randint(4, 12)
		image.paste(char_img, (px, py), char_img)

	# 多色小點雜訊（覆蓋在數字與背景上）
	speckle_colors = [
		(80, 60, 50), (70, 85, 60), (110, 95, 130), (120, 75, 70), (75, 75, 80),
		(95, 70, 100), (65, 80, 65), (90, 65, 70),
	]
	for _ in range(600):
		x, y = random.randint(0, width - 1), random.randint(0, height - 1)
		image.putpixel((x, y), random.choice(speckle_colors))

	buffer = io.BytesIO()
	image.save(buffer, 'PNG')
	buffer.seek(0)
	return buffer.getvalue()


def append_hash_to_filenames(directory, extension='.txt', separator='^'):
	"""
	掃描 directory 下符合 extension 的檔案，若檔名中尚未包含 separator + hash，
	則根據檔案內容計算 CRC32 並重新命名為 原名 separator hash extension。
	若目錄不存在則略過。
	"""
	if not directory or not os.path.isdir(directory):
		return
	for filename in os.listdir(directory):
		if not filename.endswith(extension):
			continue
		if separator in filename:
			continue
		filepath = os.path.join(directory, filename)
		if not os.path.isfile(filepath):
			continue
		try:
			with open(filepath, 'rb') as f:
				content = f.read()
			crc = zlib.crc32(content) & 0xFFFFFFFF
			hash_suffix = f"{crc:08x}"
			base = filename[: -len(extension)]
			new_name = f"{base}{separator}{hash_suffix}{extension}"
			new_path = os.path.join(directory, new_name)
			if new_path != filepath and not os.path.exists(new_path):
				os.rename(filepath, new_path)
		except Exception:
			pass



# =========================================================================
# 圖片轉 WebP 模組化工具 (含 mtime 比對增量更新與 PNG 透明度相容機制)
# =========================================================================

# --- [ 通用模組化 WebP 轉換函式 ] ---
def convert_image_to_webp(source_dir, target_dir, original_filename, quality=80):
	"""
	- 包含 mtime 覆寫原圖自動偵測更新與 PNG 透明度相容機制
	- source_dir: 原始圖片資料夾絕對路徑 (例如: media/news_2/img)
	- target_dir: WebP 儲存目標資料夾絕對路徑 (例如: media/news_2/img/thumb-webp)
	- original_filename: 原始圖片檔名 (例如: "banner1.jpg")
	- quality: 壓縮品質 (預設 80 %)
	"""
	if Image is None or not original_filename:
		return ""

	original_path = os.path.join(source_dir, original_filename)
	name_without_ext = os.path.splitext(original_filename)[0]
	webp_filename = f"{name_without_ext}.webp"
	webp_path = os.path.join(target_dir, webp_filename)

	# --- 1. 檢查原始圖片是否存在 ---
	if not os.path.exists(original_path):
		return ""

	# --- 2. 核心增量比對 (含檔案修改時間 mtime) ---
	should_convert = False
	if not os.path.exists(webp_path):
		should_convert = True
	else:
		# 當維護人員手動上傳覆寫原圖時，原圖修改時間戳記會大於 WebP 的修改時間戳記
		original_mtime = os.path.getmtime(original_path)
		webp_mtime = os.path.getmtime(webp_path)
		if original_mtime > webp_mtime:
			should_convert = True

	# --- 3. 取得相對於 MEDIA_ROOT 的快取 WebP 路徑 ---
	relative_webp_path = os.path.relpath(webp_path, settings.MEDIA_ROOT).replace("\\", "/")

	if not should_convert:
		return relative_webp_path

	# --- 4. 使用 FileLock 機制防止高流量/快速重新整理時的重複轉檔與 CPU 暴衝 ---
	if FileLock is not None:
		lock_path = f"{webp_path}.lock"
		with FileLock(lock_path):
			# 雙重確認等待鎖定期間是否已由其他線程完成轉檔
			if os.path.exists(webp_path) and os.path.getmtime(webp_path) >= os.path.getmtime(original_path):
				return relative_webp_path

			return _execute_webp_save(original_path, webp_path, quality, relative_webp_path)
	else:
		return _execute_webp_save(original_path, webp_path, quality, relative_webp_path)


# --- [ 核心 WebP 儲存函式 ] ---
def _execute_webp_save(original_path, webp_path, quality, relative_webp_path):
	try:
		with Image.open(original_path) as img:
			# --- 5. PNG 透明度與色彩空間防堵機制 (Alpha Channel) ---
			if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
				img = img.convert('RGBA')
			else:
				img = img.convert('RGB')
			# --- 6. 保存為高品質 WebP ---	
			img.save(webp_path, 'WEBP', quality=quality)
		return relative_webp_path
	except Exception as e:
		print(f"[WebP Error] 轉檔失敗: {e}")
		return ""


# --- [ 通用 PDF 轉 WebP 圖片函式 (集中化集中管理) ] ---
def convert_pdf_to_webp(source_dir, target_dir, pdf_filename, quality=100):
	"""
	將 PDF 檔案自動轉換為 WebP 圖片（支援多頁 PDF，集中管理）
	- source_dir: PDF 來源資料夾
	- target_dir: WebP 目標儲存資料夾
	- pdf_filename: PDF 檔名（如 '2025-health-project.pdf'）
	- quality: 壓縮品質 (預設 100 %)
	回傳：WebP 圖片相對路徑列表 與 是否剛完成新轉檔 (tuple)
	"""
	if fitz is None or Image is None:
		print("[錯誤] 未安裝 fitz (PyMuPDF) 或 PIL，無法進行 PDF 轉檔")
		return [], False
		
	os.makedirs(target_dir, exist_ok=True)
	pdf_path = os.path.join(source_dir, pdf_filename)

	if not os.path.exists(pdf_path):
		print(f"[錯誤] 找不到 PDF 檔案：{pdf_path}")
		return [], False

	pdf_basename = os.path.splitext(pdf_filename)[0]
	lock_path = os.path.join(target_dir, f"{pdf_basename}.lock")
	
	newly_converted = False
	
	# 執行檔案鎖安全轉檔
	if FileLock is not None:
		with FileLock(lock_path):
			first_page_webp = os.path.join(target_dir, f"{pdf_basename}-page1.webp")
			if not os.path.exists(first_page_webp):
				newly_converted = True
				_execute_pdf_to_webp(pdf_path, target_dir, pdf_basename, quality)
	else:
		first_page_webp = os.path.join(target_dir, f"{pdf_basename}-page1.webp")
		if not os.path.exists(first_page_webp):
			newly_converted = True
			_execute_pdf_to_webp(pdf_path, target_dir, pdf_basename, quality)
			
	# 整理並回傳已轉換的圖片相對路徑
	webp_files = []
	page = 1
	while True:
		webp_filename = f"{pdf_basename}-page{page}.webp"
		webp_path = os.path.join(target_dir, webp_filename)
		if os.path.exists(webp_path):
			relative_path = os.path.relpath(webp_path, settings.MEDIA_ROOT).replace("\\", "/")
			webp_files.append(relative_path)
			page += 1
		else:
			break

	return webp_files, newly_converted


def _execute_pdf_to_webp(pdf_path, target_dir, pdf_basename, quality):
	try:
		pdf_document = fitz.open(pdf_path)
		page_count = pdf_document.page_count
		for page_num in range(page_count):
			page = pdf_document[page_num]
			mat = fitz.Matrix(2, 2)  # 2倍縮放高清晰度
			pix = page.get_pixmap(matrix=mat)
			img_data = pix.tobytes("png")
			image = Image.open(io.BytesIO(img_data))

			webp_filename = f"{pdf_basename}-page{page_num + 1}.webp"
			webp_path = os.path.join(target_dir, webp_filename)
			image.save(webp_path, 'WEBP', quality=quality)

		pdf_document.close()
	except Exception as e:
		print(f"[PDF Error] 轉換失敗 {pdf_basename}: {e}")


# --- [ 安全清理機制 ] ---
def safe_cleanup_webp_cache(source_dir, target_dir):
	"""
	安全清理機制：僅移除 target_dir 快取資料夾下對應原圖已被刪除的孤立 WebP 與鎖定檔，
	絕對不會修改或刪除 source_dir 原始資料夾底下的任何檔案。
	"""
	if not os.path.exists(target_dir) or not os.path.exists(source_dir):
		return
	for filename in os.listdir(target_dir):
		if filename.endswith('.webp'):
			name_without_ext = os.path.splitext(filename)[0]
			# 檢查原始資料夾中是否存在任何同名原圖 (支援多種常見副檔名)
			has_original = False
			for ext in ['.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF']:
				if os.path.exists(os.path.join(source_dir, f"{name_without_ext}{ext}")):
					has_original = True
					break

			# 若原圖已不存在，安全清除該快取
			if not has_original:
				webp_filepath = os.path.join(target_dir, filename)
				lock_filepath = f"{webp_filepath}.lock"
				try:
					os.remove(webp_filepath)
					if os.path.exists(lock_filepath):
						os.remove(lock_filepath)
				except OSError:
					pass
# =========================================================================
# 通用寄信模組
# =========================================================================
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def send_generic_html_email(subject, template_name, context, recipient_list):
	"""
	通用寄信函式
	- subject: 信件主旨
	- template_name: HTML 版型路徑 (例如 'email/common_feedback_email.html')
	- context: 傳入版型的參數字典 (例如 {'form_data': {'姓名': '王大明', ...}})
	- recipient_list: 收件者列表
	"""
	if not recipient_list:
		return False
	
	try:
		html_message = render_to_string(template_name, context)
		email = EmailMessage(
			subject=subject,
			body=html_message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			to=recipient_list,
		)
		email.content_subtype = "html"  # 重要: 設為 HTML 格式
		email.send(fail_silently=False)
		return True
	except Exception as e:
		print(f"[Email Error] 寄信失敗: {e}")
		return False

# =========================================================================
# 共用驗證碼 HTTP API 端點 (原於 views.py，為避免混淆移至此)
# =========================================================================
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from Pomelo_test.decorators import ratelimit_captcha
import time
# random 已在上方 import

@never_cache
def common_captcha_img(request):
	"""回傳驗證碼 PNG 圖片供全站共用"""
	try:
		# 生成 5 位數字驗證碼
		code = "".join(str(random.randint(0, 9)) for _ in range(5))
		# 存入 session，設定統一的 captcha key
		request.session['common_captcha_code'] = code
		# 設定驗證碼產生時間，用於計算是否過期
		request.session['common_captcha_timestamp'] = time.time()
		
		image_bytes = generate_captcha_image_bytes(code)
		return HttpResponse(image_bytes, content_type='image/png')
	except Exception as e:
		return HttpResponse(status=500)

@never_cache
@ratelimit_captcha(max_requests=10, window=60)
def common_refresh_captcha(request):
	"""刷新驗證碼並回傳新的圖片 URL"""
	# 回傳加上時間戳記以避免瀏覽器快取
	return JsonResponse({
		'success': True,
		'captcha_url': f'/api/captcha/image/?t={int(time.time())}'
	})

