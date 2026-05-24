from django.conf import settings # 取得專案 (setting.py) 內的變數跟設定
from django.shortcuts import render, Http404, redirect # 網頁渲染至 HTML 頁面 / 例外類型 用來找不到資源時，丟出 404 頁面 / 重導向 (302、303)，常用於 POST 成功後的 PRG（避免重複提交）
from django.http import JsonResponse, HttpResponse, FileResponse # 回傳不同類型的 HTTP 回應
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger # 用於分頁並處理例外情況
from collections import defaultdict, OrderedDict # 用於分群或累加資料 / 用於需要穩定排序的回傳資料
from django.utils.html import escape # 用於轉義 HTML 字元，避免 XSS 攻擊
from django.views.decorators.http import require_GET # 限制只能用 GET 方法存取的裝飾器
import os, oracledb, datetime, re, time, random, traceback # 用於掃描資料夾與讀取 txt 檔 / 連接 Oracle 資料庫 / 處理日期時間 / 解析檔名、從文字抽出影片 id 或標籤

from django.contrib import messages # Django 內建訊息 (成功 / 失敗) 框架

# 新修改 (圖片轉 WebP、PDF 轉 WebP 工具)
from Pomelo_test.utils import generate_captcha_image_bytes, convert_image_to_webp, convert_pdf_to_webp
from Pomelo_test.decorators import ratelimit_form_submit, captcha_failure_limit

from .forms import ContactForm, send_email_to_client
# ContactForm：Django 表單類別，用來驗證使用者輸入（name/email/subject/message 等）
# send_email_to_client：封裝郵件內容與發送邏輯的函式（使用 Django 的郵件後端發送 EmailMessage）。


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 資料庫設定 ■■■■■■■■■■■■■■■■■■■■■■■■■■
case_plsql_host = settings.CASE_PLSQL_HOST
case_plsql_db = settings.CASE_PLSQL_DB
case_plsql_user = settings.CASE_PLSQL_USER
case_plsql_pwd = settings.CASE_PLSQL_PWD


# HIS資料庫相關程式
class PLSQLAPI:
	@staticmethod
	def get_connection():
		return oracledb.connect(user=case_plsql_user, password=case_plsql_pwd, dsn=f"{case_plsql_host}/{case_plsql_db}")

	@staticmethod
	def Search_Stop_Show(date):
		connection = None
		try:
			# 連線Oracle資料庫
			connection = PLSQLAPI.get_connection()
		except Exception as e:
			print(f"Oracle connection failed in Search_Stop_Show: {e}")
			return []

		try:
			# 輸入你要查找的資料表語法
			# 使用 :param_name 作為佔位符
			sql = '''SELECT SEC_SENAME,EMP_EMPNAME,SUBSTR(SCD_VISITDT,7,8),SCD_SHIFTNO,SCD_ROOMNO FROM REGSCD
			INNER JOIN BASEMP
				ON SCD_EMPNO = EMP_EMPNO 
			INNER JOIN BASSECT
				ON SCD_SECTNO = SEC_SECTNO
			WHERE SCD_CANCEL = 'Q'
				AND SCD_VISITDT LIKE :date || '%'
				AND EMP_DC = 'N'
			ORDER BY SCD_VISITDT,SCD_SHIFTNO'''
			# 定義資料庫游標
			c = connection.cursor()
			c.execute(sql, {'date': date})

			rows = c.fetchall()

			c.close()
			connection.close()

			# 回傳第一比查詢資料(rows[0])
			return(rows)
		except Exception as e:
			print(f"SQL execution failed in Search_Stop_Show: {e}")
			try:
				c.close()
			except:
				pass
			try:
				connection.close()
			except:
				pass
			return []

	@staticmethod
	def Search_Stop_Show_by_Dr(patid, sectno=None, connection=None): # ---【 Modify-多綁定科別 】---
		should_close = False
		if connection is None:
			try:
				# 連線Oracle資料庫
				connection = PLSQLAPI.get_connection()
				should_close = True
			except Exception as e:
				print(f"Oracle connection failed in Search_Stop_Show_by_Dr: {e}")
				return []

		today = datetime.datetime.now()
		n_date = today.strftime("%Y%m%d")
		e_date = (today + datetime.timedelta(days = 60)).strftime("%Y%m%d")

		try:
			# 輸入你要查找的資料表語法
			# ---【 Modify-根據是否有傳入 sectno 決定 SQL 條件 】Start 至 REGSCD End ---
			# ---【 ADD-多綁科別-{sectno_cond}】
			sectno_cond = "AND SCD_SECTNO = :sectno" if sectno and str(sectno).strip() else ""

			sql = f'''SELECT SEC_SENAME,EMP_EMPNAME,SCD_VISITDT,SCD_SHIFTNO,SCD_ROOMNO FROM REGSCD 
			INNER JOIN BASEMP
				ON SCD_EMPNO = EMP_EMPNO 
			INNER JOIN BASSECT
				ON SCD_SECTNO = SEC_SECTNO
			WHERE SCD_CANCEL = 'Q'
				AND SCD_EMPNO = :patid
				{sectno_cond}
				AND SCD_VISITDT BETWEEN :n_date AND :e_date
				AND EMP_DC = 'N'
			ORDER BY SCD_VISITDT'''
			# 定義資料庫游標
			c = connection.cursor()
			# ---【 ADD-動態參數綁定：若前端有傳入 sectno 才加入字典，避免 SQL 報錯 Start 】---
			params = {'patid': patid, 'n_date': n_date, 'e_date': e_date}
			if sectno and str(sectno).strip():
				params['sectno'] = sectno
			# ---【 ADD-動態參數綁定 End 】---
			c.execute(sql, params)

			rows = c.fetchall()
			datas = []

			for row in rows:
				datas.append(list(row))

			i = 0
			for data in datas:
				datas[i].append(data[2][4:6])
				datas[i].append(data[2][6:8])

				if (data[3] == "1"):
					datas[i][3] = "早診"
				elif (data[3] == "2"):
					datas[i][3] = "午診"
				elif (data[3] == "3"):
					datas[i][3] = "晚診"

				i += 1

			c.close()
			if should_close:
				connection.close()

			# 回傳第一比查詢資料(rows[0])
			return(datas)
		except Exception as e:
			print(f"SQL execution failed in Search_Stop_Show_by_Dr: {e}")
			try:
				c.close()
			except:
				pass
			if should_close:
				try:
					connection.close()
				except:
					pass
			return []


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 聯絡我們 ■■■■■■■■■■■■■■■■■■■■■■■■■■
@ratelimit_form_submit(max_requests=5, window=300, redirect_url='send_mail')  # 5 分鐘內最多 5 次提交
@captcha_failure_limit(max_failures=5, lockout_time=300, redirect_url='send_mail', captcha_field='captcha')  # 5 次驗證碼錯誤後鎖定 5 分鐘
def send_mail(request):
	"""
	GET: 顯示表單
	POST: 驗證表單並寄信（支援 AJAX 和普通提交）
	"""

	CAPTCHA_EXPIRY = 120  # 驗證碼有效時間（秒），改為 2 分鐘

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
				return render(request, "specialty_health/h-contact.html", {
					"form": form,
					'og_image': '',
					'ga_id': '',
					'gtm_id': ''
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
					return redirect('health_send_mail')
			except Exception as e:
				import logging
				logging.exception("send_mail failed in health contact view")
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
			return render(request, "specialty_health/h-contact.html", {
				"form": form,
				'og_image': '',
				'ga_id': '',
				'gtm_id': ''
			})
	else:
		form = ContactForm()

	return render(request, "specialty_health/h-contact.html", {
		"form": form,
		'og_image': '',
		'ga_id': '',
		'gtm_id': ''
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 共用檔案路徑 ■■■■■■■■■■■■■■■■■■■■■■■■■■

# 連動官網-各科醫師個人介紹 txt 檔案
dirs = [
	os.path.join(settings.MEDIA_ROOT, 'department', 'D000_4_婦兒科', '1_婦科_Gynecology'),
	os.path.join(settings.MEDIA_ROOT, 'department', 'D000_2_內科', '5_肝膽腸胃科_Gastroenterology'),
	os.path.join(settings.MEDIA_ROOT, 'department', 'D000_2_內科', '8_家醫科_FamilyMedicine'),
	os.path.join(settings.MEDIA_ROOT, 'department', 'D000_1_外科', '1_骨科_Orthopedic'),
]

# 連動官網-相關文章、影音專區 txt 檔案及 txt 檔案中的圖片 (壓縮後-縮圖用)
article_dir = os.path.join(settings.MEDIA_ROOT, 'news_2')
video_dir = os.path.join(settings.MEDIA_ROOT, 'news_3')
media_base_dir = os.path.join(settings.MEDIA_ROOT, 'news_2', 'img')

# 健檢專網獨立(專案資料夾路徑設定)
special_base_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_health') # 主資料夾
health_item_dir = os.path.join(special_base_dir, 'h-articles') # 子資料夾-健檢專案

# 健檢專網獨立(''最新消息'' txt 檔及壓縮後-縮圖用圖片)：
NEWS_DIR = os.path.join(special_base_dir, 'h-news')
news_img_dir = os.path.join(special_base_dir, 'h-news', 'img')

# 健檢專網獨立(衛教資訊)：
Films_Dir = os.path.join(special_base_dir, 'h-films')




# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 共用函式 ■■■■■■■■■■■■■■■■■■■■■■■■■■



# === 工具：處理包在段落中的 <img1> 與 <yt> 轉換 html 邏輯 【用於 parse_article_txt() 呼叫】 ===
def render_custom_tags(line, img_url):
	'''
	專門用來處理 <t> 段落文字中內嵌的自定標籤
	將 <img1> 替換成 <img>，<yt> 替換成 <iframe>
	變成 HTML 可直接放進模板渲染
	'''
	if '<img1>' in line:
		parts = line.split('<img1>')
		for part in parts[1:]:
			filename = part.strip().split()[0].split('</')[0]
			webp_path = convert_item_article_image_to_webp(filename)
			if webp_path:
				img_tag = f'<img src="/media/{webp_path}" class="img-fluid w-100">'
			else:
				img_tag = f'<img src="{img_url}/{filename}" class="img-fluid w-100">'
			line = line.replace(f'<img1>{filename}', img_tag)

	if '<yt>' in line:
		yt_url = line.replace('<yt>', '').strip()
		line = f'<div class="info_iframe"><iframe src="{yt_url}" frameborder="0" allowfullscreen sandbox="allow-same-origin allow-scripts"></iframe></div>'

	return line

# === txt 標籤內容拆解：負責逐行處理 <t>、<yt>、<img1>等開頭的段落 ===
def parse_article_txt(filepath, detail=True):
	'''
	將 txt 裡面的標籤進行拆解處理，讓之後其他程式讀取檔案進來時，加入這段函式，就可以依照各個標籤設置不同 css
	目前用於：醫師「相關文章-卡片項目、文章獨立頁內容」、媒體報導、最新消息、治療項目
	'''
	with open(filepath, 'r', encoding='utf-8-sig') as f:
		lines = f.readlines()

	# 根據 txt 來源資料夾路徑自動推導 img_url
	if 'news_2' in filepath:
		img_url = '/media/news_2/img'
	elif 'h-news' in filepath:
		img_url = '/media/specialty_health/h-news/img'
	elif 'h-articles-img' in filepath:
		img_url = '/media/specialty_health/h-articles/h-articles-img/img_webp_article'
	else:
		img_url = '/media'

	org_thumb_img= ""
	thumb_img = ""
	card_image = ""
	item_a_title = ""
	original_image = ""
	article_image = ""
	news_image = ""
	item_article_image = ""
	content_blocks = []
	summary = ""

	has_first_img = False

	for line in lines:
		line = line.strip()

		# (1) 處理縮圖
		if line.startswith('<thumb-img>'):
			org_thumb_img = line.replace('<thumb-img>', '').strip()
			# 治療項目縮圖 (轉 webp 格式)
			thumb_img = convert_item_icon_image_to_webp(org_thumb_img)
		
		# ← 新增：處理 PDF 自動轉 WebP 圖片
		elif line.startswith('<openpdf>'):
			if not detail:
				continue
			pdf_name = line.replace('<openpdf>', '').strip()
			
			# 根據 txt 來源路徑自動推導 PDF 來源資料夾與目標資料夾
			if 'h-news' in filepath:
				source_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_health', 'h-news', 'news-pdfs')
				target_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_health', 'h-news', 'news-pdfs', 'img_webp_pdf')
			elif 'h-articles' in filepath:
				source_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_health', 'h-articles', 'item-pdfs')
				target_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_health', 'h-articles', 'item-pdfs', 'img_webp_pdf')
			else:
				source_dir = os.path.join(settings.MEDIA_ROOT)
				target_dir = os.path.join(source_dir, 'img_webp_pdf')
			
			# 自動將 PDF 轉換為 WebP 圖片
			webp_images, is_new = convert_pdf_to_webp(source_dir, target_dir, pdf_name, quality=100)
			
			if is_new:
				print(f"[檔案下載] 已新增下載連結：{pdf_name}")
				print(f"[PDF轉換] 已將 {pdf_name} 轉換為 {len(webp_images)} 張 WebP 圖片")

			# 將每張 WebP 圖片按順序加入內容區塊（page1, page2, page3...）
			for webp_path in webp_images:
				content_blocks.append({
					'type': 'img',  # 使用 'img' 與模板的 {% elif block.type == 'img' %} 匹配
					'class': 'a-img',
					'item_article_src': webp_path  # 使用相對路徑，模板會自動加上 /media/
				})
			
			continue

		# ← 新增：處理 PDF 下載連結
		elif line.startswith('<viewpdf>'):
			if not detail:
				continue
			download_filename = line.replace('<viewpdf>', '').strip()
			
			# 根據 txt 來源路徑推導下載類型
			if 'h-news' in filepath:
				download_type = 'news'
			elif 'h-articles' in filepath:
				download_type = 'item'
			else:
				download_type = 'general'
			
			# 加入下載按鈕區塊
			content_blocks.append({
				'type': 'download',
				'class': 'download-section',
				'filename': download_filename,
				'download_type': download_type
			})
			continue

		# (2) 處理主要圖片
		elif line.startswith('<img1>'):
			if not detail and has_first_img:
				continue
			original_image = line.replace('<img1>', '').strip() # 原圖.jpg
			
			# 依來源資料夾只跑對應功能轉換圖片 (轉 webp 格式)-避免處理 any 有 <img1> 標籤時，都會同時觸發四個不同路徑的 WebP 圖片轉換
			if 'news_2' in filepath:
				# 「醫師-相關文章 / 媒體報導」
				card_image = convert_image_to_webp_separate_folder(original_image)				
				article_image = convert_article_image_to_webp(original_image)
			
			elif 'h-news' in filepath:
				# 「最新消息」文章內文圖片
				news_image = convert_news_image_to_webp(original_image)

			elif 'h-articles' in filepath or 'h-articles-img' in filepath:
				# 「健檢專案」文章內文圖片
				item_article_image = convert_item_article_image_to_webp(original_image)
			
			has_first_img = True

			if detail:
				content_blocks.append({
					'type': 'img',
					'class': 'a-img',
					'src': card_image,
					'article_src': article_image,
					'news_src': news_image,
					'item_article_src': item_article_image
				})

		elif line.startswith('<yt>'):
			if not detail:
				continue
			yt_url = line.replace('<yt>', '').strip()
			iframe_html = f'<iframe width="100%" height="315" src="{yt_url}" frameborder="0" allowfullscreen></iframe>'
			content_blocks.append({
				'type': 'embed',
				'class': 'video-embed',
				'text': iframe_html
			})

		elif line.startswith('<h01>'):
			item_a_title = line.replace('<h01>', '').strip()

		elif line.startswith('<h>'):
			if not detail:
				continue
			content_blocks.append({
				'type': 'h2',
				'class': 'article_h',
				'text': line.replace('<h>', '').strip()
			})
		elif line.startswith('<cap>'):
			if not detail:
				continue
			content_blocks.append({
				'type': 'h3',
				'class': 'title-02',
				'text': line.replace('<cap>', '').strip()
			})
		elif line.startswith('<li-t>'):
			if not detail:
				continue
			content_blocks.append({
				'type': 'ul',
				'class': 'list-title',
				'text': line.replace('<li-t>', '').strip()
			})
		elif line.startswith('<li-p>'):
			if not detail:
				continue
			content_blocks.append({
				'type': 'li',
				'class': 'list-text',
				'text': line.replace('<li-p>', '').strip()
			})
		elif line.startswith('<li-q>'):
			if not detail:
				continue
			content_blocks.append({
				'type': 'ul',
				'class': 'list-question',
				'text': line.replace('<li-q>', '').strip()
			})
		elif line.startswith('<li-a>'):
			if not detail:
				continue
			content_blocks.append({
				'type': 'li',
				'class': 'list-answer',
				'text': line.replace('<li-a>', '').strip()
			})
		elif line.startswith('<t>'):
			# 過濾整段含有「含有<a>的預約掛號」的 <t> 標籤
			if 'news_2' in filepath:  # 指定檔案來源是 news_2 才進行不顯示的程式
				if ('<a href' in line) and ('預約掛號' in line):
					continue

			text = line.replace('<t>', '').strip() # 解析到 <t> 開頭，又得到文字含 <img1> 或 <yt> 呼叫 render_custom_tags(text, ...)
			
			if not detail and summary:
				continue

			text = render_custom_tags(text, img_url=img_url) # img_url-自動判斷資料夾來源；

			if not summary:
				summary = text[:50]

			if detail:
				if text.startswith('新聞連結'):
					# 抓出所有 <a href="...">文字</a>
					links = re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', text)
					link_html = ""
					for href, label in links:
						link_html += f'<a href="{href}" class="btn btn-outline-info btn-sm mr-2" target="_blank">' \
									f'<i class="fas fa-link"></i> {label}</a>'
					content_blocks.append({
						'type': 'p',
						'class': 'news-links',  # 可額外加樣式
						'text': link_html
					})
				else:
					content_blocks.append({
						'type': 'p',
						'class': 'a-paragraph',
						'text': text
					})

	return {
		'thumb_img': thumb_img,
		'og_img_item': org_thumb_img,
		'og_img': original_image,
		'image': card_image,
		'item_a_title': item_a_title,
		'summary': summary,
		'blocks': content_blocks,
	}


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 首頁 (health_main) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ======================= 後端處理 ======================
# 後:首頁「Banner」
def convert_banner_image_to_webp(original_filename):
	"""
	專用：轉換 Banner 圖片為 WebP
	儲存路徑：media/specialty_health/banner/webp
	壓縮品質：80%
	"""
	source_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_health', 'banner')
	target_dir = os.path.join(source_dir, 'banner-webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

def health_banner_api(request):
	banner_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_health', 'banner')
	files = os.listdir(banner_dir)

	image_dict = {}
	for f in files:
		if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
			parts = f.split('_')
			if len(parts) < 3:
				continue
			key = parts[0]  # e.g., B01
			device = parts[-1].split('.')[0]  # pc / mb
			image_dict.setdefault(key, {})[device] = f

	# 讀取 banner-link.txt
	link_map = {}
	link_file = os.path.join(banner_dir, 'banner-link.txt')
	if os.path.exists(link_file):
		with open(link_file, encoding='utf-8-sig') as f:
			for line in f:
				line = line.strip()
				if line.startswith('<') and '>' in line:
					key = line.split('>')[0][1:]  # B01
					url = line.split('>')[1]
					link_map[key] = url

	# 整理排序結果
	result = []
	for key in sorted(image_dict.keys()):
		images = image_dict[key]
		pc_img = images.get('pc')
		mb_img = images.get('mb', pc_img)
		pc_webp = convert_banner_image_to_webp(pc_img) if pc_img else ""
		mb_webp = convert_banner_image_to_webp(mb_img) if mb_img else pc_webp

		result.append({
			'key': key,
			'pc': pc_img,
			'mb': mb_img,
			'pc_webp': pc_webp,
			'mb_webp': mb_webp,
			'link': link_map.get(key, None)
		})

	return JsonResponse({'banners': result})

# 後:首頁「最新消息」
@require_GET
def health_news_home_api(request):
	"""首頁用：取得最新 5 筆最新消息"""
	try:
		all_news = get_all_health_news()
		latest_news = all_news[:5]

		return JsonResponse({
			'news': [
				{
					'title': item['title'],
					'date': item['date'].strftime('%Y-%m-%d'),
					'url': item['url']
				} for item in latest_news
			]
		})
	except Exception as e:
		import traceback
		traceback.print_exc()
		return JsonResponse({'error': str(e)}, status=500)

# 後:首頁「影音專區」
@require_GET
def health_film_home_api(request):
	"""首頁「影音專區」專用 API：取得最新 3 筆影片（同時讀取 video_dir 與 Films_Dir）"""
	employee_ids = get_health_center_doctor_ids()
	all_videos = []

	# 需要掃描的資料夾（原本的 video_dir 與 新增的 Films_Dir）
	search_dirs = [video_dir, Films_Dir]

	for d in search_dirs:
		if not os.path.exists(d):
			continue

		for video_filename in os.listdir(d):
			if not video_filename.endswith('.txt'):
				continue

			# 若是原本的 video_dir，仍保留以 employee_id 過濾的邏輯
			if d == video_dir and not any(emp_id in video_filename for emp_id in employee_ids):
				continue

			filepath = os.path.join(d, video_filename)
			with open(filepath, 'r', encoding='utf-8-sig') as f:
				lines = f.read().splitlines()

			video_data = {
				'title': '',
				'date': '',
				'doctor_id': '',
				'youtube_url': '',
				'youtube_image': ''
			}

			for line in lines:
				if line.startswith('<yh>'):
					full_title = line.replace('<yh>', '').strip()
					video_data['title'] = re.split(r'[／/]', full_title)[0].strip()
				elif line.startswith('<yd>'):
					video_data['date'] = line.replace('<yd>', '').strip()
				elif line.startswith('<dr>'):
					video_data['doctor_id'] = line.replace('<dr>', '').strip()
				elif line.startswith('<ytb>'):
					ytb_url = line.replace('<ytb>', '').strip()
					video_data['youtube_url'] = ytb_url

					# 嘗試從不同格式的 youtube url 取得影片 id
					ytb_id = ''
					if 'v=' in ytb_url:
						# watch?v=xxxx 或有其他參數
						m = re.search(r'v=([^&]+)', ytb_url)
						if m:
							ytb_id = m.group(1)
					elif 'embed/' in ytb_url:
						ytb_id = ytb_url.split('embed/')[-1].split('?')[0]
					else:
						# 取最後一段 (短網址或 /vi/...)
						ytb_id = ytb_url.rstrip('/').split('/')[-1].split('?')[0]

					if ytb_id:
						video_data['youtube_image'] = f'https://img.youtube.com/vi/{ytb_id}/hqdefault.jpg'

			# 若檔案內沒提供標題，嘗試從檔名取得（例如：F003_加入「糖尿病共照網」 免費檢查好處多多.txt）
			if not video_data['title']:
				name = video_filename.replace('.txt', '')
				if '_' in name:
					video_data['title'] = name.split('_', 1)[1]
				else:
					video_data['title'] = name

			all_videos.append(video_data)

	# 按 date（字串）或無日期的項目排序，若沒有 date，會排在後面；取最新 3 筆
	all_videos.sort(key=lambda x: x.get('date', ''), reverse=True)
	latest_videos = all_videos[:3]

	return JsonResponse({'videos': latest_videos})

# 後:首頁「媒體報導」
@require_GET
def health_media_home_api(request):
	"""首頁「媒體報導」專用：只回傳最新前 3 筆媒體報導文章"""
	employee_ids = get_health_center_doctor_ids()
	all_articles = []

	for post_filename in os.listdir(article_dir):
		if not post_filename.endswith('.txt'):
			continue
		if not any(emp_id in post_filename for emp_id in employee_ids):
			continue

		parts = post_filename.split('_')
		if len(parts) < 8:
			continue

		try:
			pub_date = datetime.datetime.strptime(parts[6], "%Y-%m-%d")
		except ValueError:
			continue

		all_articles.append({
			'filename': post_filename,
			'title': parts[2],
			'pub_date': pub_date,
			'parts': parts
		})

	all_articles.sort(key=lambda x: x['pub_date'], reverse=True)
	latest_articles_meta = all_articles[:3]

	latest_articles = []
	for item in latest_articles_meta:
		parts = item['parts']
		web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"
		path = os.path.join(article_dir, item['filename'])
		parsed = parse_article_txt(path, detail=False)

		latest_articles.append({
			'title': item['title'],
			'pub_date': item['pub_date'].strftime('%Y-%m-%d'),
			'image': parsed['image'],
			'summary': parsed['summary'],
			'url': f"/specialty_health/articles/{web_url}"
		})

	return JsonResponse({'articles': latest_articles})


# === 健檢專案：分群組處理 (按序號 Txxx 整合) ===
def get_grouped_treatments():
	"""
	將健檢專案按序號 (Txxx) 進行分組。
	如果一個序號下有多個檔案，則歸類為一個主專案，主專案名稱取自檔案前綴。
	"""
	all_files = os.listdir(health_item_dir)
	serial_map = OrderedDict()
	
	# 1. 蒐集並分群
	for filename in all_files:
		if filename.endswith('.txt') and "item" in filename:
			match = re.search(r'T(\d+)', filename)
			if match:
				serial = match.group(0) # e.g. T001, T002
				if serial not in serial_map:
					serial_map[serial] = []
				serial_map[serial].append(filename)
				
	grouped_results = []
	
	# 2. 處理每一群
	for serial, files in serial_map.items():
		if len(files) == 1:
			# 單一專案：維持原樣
			filename = files[0]
			parts = filename.rsplit('_', 3)
			title = parts[2]
			url_name = parts[3].replace('.txt', '')
			
			item_path = os.path.join(health_item_dir, filename)
			item_parsed = parse_article_txt(item_path, detail=False)
			
			grouped_results.append({
				'serial': serial,
				'title': title,
				'url_name': url_name,
				'thumb_img': item_parsed['thumb_img'],
				'order': int(serial[1:]),
				'is_group': False,
				'children': []
			})
		else:
			# 多個專案：整合成一個主專案
			children = []
			main_title = ""
			main_thumb = ""
			
			# 子項目排序（按檔名）
			files.sort()
			
			for i, filename in enumerate(files):
				parts = filename.rsplit('_', 3)
				full_title = parts[2]
				url_name = parts[3].replace('.txt', '')
				
				# 拆分主標題與子標題 (e.g. 公教人員-基礎專案)
				if '-' in full_title:
					prefix, sub = full_title.split('-', 1)
					if not main_title: main_title = f"{prefix}"
					sub_title = sub
				else:
					if not main_title: main_title = full_title
					sub_title = full_title
					
				item_path = os.path.join(health_item_dir, filename)
				item_parsed = parse_article_txt(item_path, detail=False)
				
				if i == 0:
					main_thumb = item_parsed['thumb_img']
					
				children.append({
					'title': sub_title,
					'url_name': url_name,
				})
				
			grouped_results.append({
				'serial': serial,
				'title': main_title,
				'url_name': children[0]['url_name'], # 點擊主專案導向第一個子專案
				'thumb_img': main_thumb,
				'order': int(serial[1:]),
				'is_group': True,
				'children': children
			})
			
	# 按序號排序
	grouped_results.sort(key=lambda x: x['order'])
	return grouped_results


# ======================= 前端模板 ======================
def health_main(request):
	treatments = get_grouped_treatments() # 使用整合後的列表
	return render(request, "specialty_health/health-index.html", {
		'treatments': treatments,
		'og_image': '',
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 關於我們 (ort_about) ■■■■■■■■■■■■■■■■■■■■■■■■■■
def health_about(request):
	return render(request, "specialty_health/h-about-us.html", {
		'og_image': '',
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 醫師陣容 (doctor_list) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ======================= 後端處理 =======================
# 後:醫師相關文章圖片轉 webp 格式
def convert_image_to_webp_separate_folder(original_filename):
	"""
	專用：轉換「醫師相關文章-卡片縮圖」為 WebP
	儲存路徑：media/news_2/img/thumb-webp
	壓縮品質：50%
	"""
	source_dir = media_base_dir
	target_dir = os.path.join(source_dir, 'thumb-webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=50)

def convert_article_image_to_webp(original_filename):
	"""
	專用：轉換「醫師相關文章-內文圖片」為 WebP
	儲存路徑：media/news_2/img/img_webp_article
	壓縮品質：80%
	"""
	source_dir = media_base_dir
	target_dir = os.path.join(source_dir, 'img_webp_article')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)


# 後:醫師個人照轉 webp 格式
def convert_doctor_image_to_webp(original_filename):
	"""
	專用：轉換醫師照片為 WebP
	儲存路徑：media/department/img/webp
	壓縮品質：80%
	"""
	source_dir = os.path.join(settings.MEDIA_ROOT, 'department', 'img')
	target_dir = os.path.join(source_dir, 'doc-webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

# 後:醫師「個人介紹」- 個人照、專長、學經歷
def parse_doctor_txt(content):
	'''	醫師「個人介紹」，txt 標籤內容進行拆解處理，再個別帶入「個人介紹」'''
	result = {
		'philosophy': '',
		'expertise': '',
		'expertise_list': [],
		'education': '',
		'education_list': [],
		'image': ''
	}
	lines = content.strip().splitlines()
	for line in lines:
		if line.startswith('i'):
			result['philosophy'] = line.replace('<i>', '').strip()
		elif line.startswith('<e>'):
			expertise = line.replace('<e>', '').strip()
			result['expertise'] = expertise
			result['expertise_list'] = [item.strip() for item in expertise.split('、') if item.strip()]
		elif line.startswith('<a>'):
			education = line.replace('<a>', '').strip()
			result['education'] = education
			result['education_list'] = [item.strip() for item in education.split('；') if item.strip()]
		elif line.startswith('<img1>'):
			result['image'] = line.replace('<img1>', '').strip()
	return result

# 後:從科別資料夾路徑中提取乾淨的中文科別名稱（例："8_家醫科_FamilyMedicine" -> "家醫科"）
def get_clean_department_name(dir_path):
	folder_name = os.path.basename(dir_path)
	parts = folder_name.split('_')
	return parts[1] if len(parts) > 1 else parts[0]

# 後:從科別資料夾路徑中提取乾淨的英文科別名稱（例："8_家醫科_FamilyMedicine" -> "FamilyMedicine"）
def get_clean_department_en(dir_path):
	folder_name = os.path.basename(dir_path)
	parts = folder_name.split('_')
	return parts[2] if len(parts) > 2 else ''

# 後:醫師「個人介紹」- 側邊選單：其他醫師
@require_GET
def doctor_sidenav_api(request):
	'''
	後端程式處理：醫師「個人介紹」頁中「側邊選單」帶入其他醫師選項列表，按科別分類
	'''
	sidenav_doctors_by_department = []

	# 遍歷所有科別路徑
	for dir_path in dirs:
		if not os.path.exists(dir_path):
			continue  # 如果路徑不存在，跳過

		# 提取科別名稱與英文名稱
		department_name = get_clean_department_name(dir_path)
		department_en = get_clean_department_en(dir_path)

		# 取得該科別下的所有醫師
		doctors = []
		for doc_filename in os.listdir(dir_path):
			if doc_filename.endswith('.txt') and "D000" in doc_filename:
				try:
					parts = doc_filename.rsplit('_', 1)
					emp_id = parts[1].replace('.txt', '')
					name_title = parts[0].split('_', 2)[-1]
					name_parts = name_title.split(' ')
					name = name_parts[0]
					job_title = name_parts[1] if len(name_parts) > 1 else ''
					# 提取科別名稱
					department_name = get_clean_department_name(dir_path)
					department_en = get_clean_department_en(dir_path)

					doctors.append({
						'employee_id': emp_id,
						'name': name,
						'job_title': job_title,
						'department': department_name,  # 加入科別名稱
						'department_en': department_en,  # 加入英文科別名稱
					})
				except Exception as e:
					print(f"錯誤解析 {doc_filename}：{e}")
					continue

		# 按醫師姓名排序
		doctors.sort(key=lambda x: x['name'])

		# 將該科別的醫師加入分類列表
		sidenav_doctors_by_department.append({
			'department': department_name,
			'department_en': department_en,  # 加入英文科別名稱
			'doctors': doctors,
		})
	
	# 按科別順序排序
	sidenav_doctors_by_department.sort(key=lambda x: DEPARTMENT_ORDER.get(x['department'], 999))

	return JsonResponse({'departments': sidenav_doctors_by_department})

# 後:停休診日期時間
def group_stops_by_month(stop_list):
	'''將「停休診日期時間」進行按月份分群組，個別傳給模板'''
	grouped = defaultdict(list)
	for stop in stop_list:
		date_str = stop[2]  # e.g. '20250516'
		dt = datetime.datetime.strptime(date_str, "%Y%m%d")
		key = dt.strftime("%Y-%m")  # 例如：'2025-05'
		grouped[key].append({
			'date': dt.strftime("%m / %d"),
			'period': stop[3],
			'room': stop[4],
		})
	# return dict(grouped)
	return dict(sorted(grouped.items()))  # 會自動按年月順序排序 (由近到遠-最新排前面)

def api_stop_info(request, employee_id):
	'''
	觸發「停休診時間」按鈕，透過 API 取值
	'''
	try:
#		※ Debug-用「假資料」測試 API 回傳值是否成功 ※
#		fake_data = [
# 			['骨科', '洪舜奕', '20250516', '午診', '1112'],
# 			['骨科', '洪舜奕', '20250616', '晚診', '1113']
# 		]
# 		stop_grouped = group_stops_by_month(fake_data)


#		透過 API 回傳資料庫「停休診時間」的值
		stop_raw = PLSQLAPI.Search_Stop_Show_by_Dr(employee_id)
		stop_grouped = group_stops_by_month(stop_raw) if stop_raw else {}

		return JsonResponse({'stop_info': stop_grouped})
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)


# 後:醫師「相關文章、文章獨立頁」
def get_related_articles(employee_id):
	'''後端程式處理：醫師「相關文章-卡片項目」，用員工 employee_id，帶入與該醫師有關的文章列表'''
	doc_articles = []
	for post_filename in os.listdir(article_dir):
		if post_filename.endswith('.txt') and employee_id in post_filename:
			parts = post_filename.split('_')
			if len(parts) < 8: # 指要要切成幾塊，會影響後面取值順序
				continue
			title = parts[2]
			date = parts[6]
			try:
				# 假設 date 格式為 YYYY-MM-DD，如 2025-04-15
				pub_date = datetime.datetime.strptime(date, "%Y-%m-%d")
			except ValueError:
				continue  # 日期格式錯誤就跳過

			web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"  # 簡短網址
			path = os.path.join(article_dir, post_filename)
			parsed = parse_article_txt(path, detail=False)

			doc_articles.append({
				'title': title,
				'pub_date': pub_date,
				'image': parsed['image'],
				'summary': parsed['summary'],
				'blocks': parsed['blocks'],
				# 'filename': filename.replace('.txt', ''),
				'filename': web_url,
				# 'web_url': web_url,
			})
	# return doc_articles
	# 根據 pub_date 做由新到舊排序
	doc_articles.sort(key=lambda x: x['pub_date'], reverse=True)
	return doc_articles

def parse_article_filename(parse_filename):
	"""
	文章獨立頁內容 (標題、發布日期、tag)
	解析檔名：編號_^_標題_^_企劃室_^_日期_^_employee_id
	"""
	parts = parse_filename.replace('.txt', '').split('_')
	return {
		'title': parts[2],
		# 'category': parts[3],
		'pub_date': parts[6],
		'employee_id': parts[7],
		'filename': parse_filename.replace('.txt', '')
	}

def extract_tags_from_blocks(blocks):
	"""從段落中找出關鍵詞做為 tags (可客製)"""
	tags = set()
	for block in blocks:
		if '骨折' in block.get('text', ''):
			tags.add('骨折')
		if '手術' in block.get('text', ''):
			tags.add('手術')
	return list(tags)

@require_GET
def get_related_articles_api(request, employee_id):
	'''後端 API-支援文章 Ajax 分頁'''
	try:
		page = int(request.GET.get("page", 1))
		# per_page = 3  # 每頁筆數
		per_page = int(request.GET.get("per_page", 3)) # 改為可動態接收

		all_articles = get_related_articles(employee_id)
		paginator = Paginator(all_articles, per_page)
		page_obj = paginator.get_page(page)

		data = [{
			'title': a['title'],
			'summary': a['summary'],
			'image': a['image'],
			'pub_date': a['pub_date'].strftime('%Y-%m-%d'),
			'url': f"/specialty_health/articles/{a['filename']}"
		} for a in page_obj]

		return JsonResponse({
			'articles': data,
			'current_page': page_obj.number,
			'num_pages': paginator.num_pages,
		})
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)


# 後：隨機取得 5 筆媒體報導文章（供 article_detail 側欄卡片用）
@require_GET
def random_health_reports_api(request):
	"""隨機取得 5 筆媒體報導文章（供 article_detail 側欄卡片用）"""
	employee_ids = get_health_center_doctor_ids()
	all_articles_meta = []

	for post_filename in os.listdir(article_dir):
		if not post_filename.endswith('.txt'):
			continue
		if not any(emp_id in post_filename for emp_id in employee_ids):
			continue

		parts = post_filename.split('_')
		if len(parts) < 8:
			continue

		try:
			pub_date = datetime.datetime.strptime(parts[6], "%Y-%m-%d")
		except ValueError:
			continue

		all_articles_meta.append({
			'filename': post_filename,
			'title': parts[2],
			'pub_date': pub_date,
			'parts': parts
		})

	# 隨機挑選 5 筆
	random_meta = random.sample(all_articles_meta, min(5, len(all_articles_meta)))

	random_articles = []
	for item in random_meta:
		parts = item['parts']
		web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"
		path = os.path.join(article_dir, item['filename'])
		parsed = parse_article_txt(path, detail=False)

		random_articles.append({
			'title': item['title'],
			'pub_date': item['pub_date'].strftime('%Y-%m-%d'),
			'image': parsed['image'],
			'summary': parsed['summary'],
			'url': f"/specialty_health/articles/{web_url}",
			'filename': web_url
		})

	return JsonResponse({'articles': random_articles})

# 後:醫師「影音專區」
def get_related_video(employee_id):
	'''	醫師「影音專區」，用員工 employee_id，帶入與該醫師有關的影音列表 '''
	video_articles = []

	for video_filename in os.listdir(video_dir):
		if video_filename.endswith('.txt'):
			parts = video_filename.replace('.txt', '').split('_')
			if len(parts) >= 4 and parts[-1] == employee_id:
				filepath = os.path.join(video_dir, video_filename)
				with open(filepath, 'r', encoding='utf-8-sig') as f: # 原 utf-8 開啟 .txt 檔案讀取第一行帶入的亂碼 (清除 BOM-順利取<yh>值)
					lines = f.read().splitlines()
					video = {
						'ytb_title': '',
						'ytb_date': '',
						'ytb_url': '',
						'ytb_id': '',
						'thumb_url': ''
					}
					for line in lines:
						if line.startswith('<yh>'):
							# video['ytb_title'] = line.replace('<yh>', '').strip()
							full_title = line.replace('<yh>', '').strip()
							video['ytb_title'] = re.split(r'[／/]', full_title)[0].strip()
						elif line.startswith('<yd>'):
							video['ytb_date'] = line.replace('<yd>', '').strip()
						elif line.startswith('<ytb>'):
							ytb_url = line.replace('<ytb>', '').strip()
							video['ytb_url'] = ytb_url
							# 取得影片 ID
							if 'embed/' in ytb_url:
								ytb_id = ytb_url.split('embed/')[1]
								video['ytb_id'] = ytb_id
								video['thumb_url'] = f'https://img.youtube.com/vi/{ytb_id}/hqdefault.jpg'
					video_articles.append(video)

	# return video_articles
	# 根據 ytb_date 做由新到舊排序
	video_articles.sort(key=lambda x: x['ytb_date'], reverse=True)
	return video_articles

@require_GET
def video_section_ajax(request, employee_id):
	'''後端 API-支援影片 Ajax 分頁'''
	try:
		page = int(request.GET.get("page", 1))
		per_page = int(request.GET.get("per_page", 3))

		videos = get_related_video(employee_id)
		paginator = Paginator(videos, per_page)
		page_obj = paginator.get_page(page)

		data = [{
			'ytb_title': v['ytb_title'],
			'ytb_date': v['ytb_date'],
			'ytb_url': v['ytb_url'],
			'thumb_url': v['thumb_url'],
		} for v in page_obj]

		return JsonResponse({
			'videos': data,
			'current_page': page_obj.number,
			'num_pages': paginator.num_pages,
		})
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)


# ======================= 前端模板 =======================
# 定義科別的顯示順序
DEPARTMENT_ORDER = {
	"家醫科": 1,
	"肝膽腸胃科": 2,
	"婦科": 3
}
def doctor_list(request):
	'''建立「醫師列表」頁，按科別分類顯示'''
	doctors_by_department = []

	# 健檢中心專用科別路徑（排除骨科）
	health_dirs = [
		os.path.join(settings.MEDIA_ROOT, 'department', 'D000_4_婦兒科', '1_婦科_Gynecology'),
		os.path.join(settings.MEDIA_ROOT, 'department', 'D000_2_內科', '5_肝膽腸胃科_Gastroenterology'),
		os.path.join(settings.MEDIA_ROOT, 'department', 'D000_2_內科', '8_家醫科_FamilyMedicine'),
	]

	# 遍歷健檢中心相關科別路徑（排除骨科）
	for dir_path in health_dirs:
		if not os.path.exists(dir_path):
			continue  # 如果路徑不存在，跳過

		# 提取科別名稱與英文名稱
		department_name = get_clean_department_name(dir_path)
		department_en = get_clean_department_en(dir_path)

		# 取得該科別下的所有醫師
		doctors = []
		for doc_filename in os.listdir(dir_path):
			if doc_filename.endswith('.txt') and "D000" in doc_filename:
				try:
					parts = doc_filename.rsplit('_', 1)
					emp_id = parts[1].replace('.txt', '')
					name_title = parts[0].split('_', 2)[-1]
					name_parts = name_title.split(' ')
					name = name_parts[0]
					job_title = name_parts[1] if len(name_parts) > 1 else ''
					# 提取科別名稱
					department_name = get_clean_department_name(dir_path)
					department_en = get_clean_department_en(dir_path)

					with open(os.path.join(dir_path, doc_filename), 'r', encoding='utf-8') as f:
						parsed = parse_doctor_txt(f.read())

					webp_image = convert_doctor_image_to_webp(parsed['image']) if parsed['image'] else ''

					doctors.append({
						'employee_id': emp_id,
						'name': name,
						'job_title': job_title,
						'expertise': parsed['expertise'],
						'image': parsed['image'],
						'image_webp': webp_image,
						'department': department_name,  # 加入科別名稱
						'department_en': department_en,  # 加入英文科別名稱
					})
				except Exception as e:
					print(f"錯誤解析 {doc_filename}：{e}")
					continue

		# 按醫師姓名排序
		doctors.sort(key=lambda x: x['name'])

		# 將該科別的醫師加入分類列表
		doctors_by_department.append({
			'department': department_name,
			'department_en': department_en,  # 加入英文科別名稱
			'doctors': doctors,
		})

	# 按科別順序排序
	doctors_by_department.sort(key=lambda x: DEPARTMENT_ORDER.get(x['department'], 999))

	return render(request, 'specialty_health/h-doctor-list.html', {
		'doctors_by_department': doctors_by_department,
		'og_image': '',
		'ga_id': '', 
		'gtm_id': ''
	})

def doctor_profile(request, employee_id):
	'''「個人介紹」頁'''
	matched_file = None
	matched_dir = None
	name = None
	name_and_title = None
	job_title = None
	department = None

	# 健檢中心專用科別路徑（排除骨科）
	health_dirs = [
		os.path.join(settings.MEDIA_ROOT, 'department', 'D000_4_婦兒科', '1_婦科_Gynecology'),
		os.path.join(settings.MEDIA_ROOT, 'department', 'D000_2_內科', '5_肝膽腸胃科_Gastroenterology'),
		os.path.join(settings.MEDIA_ROOT, 'department', 'D000_2_內科', '8_家醫科_FamilyMedicine'),
	]

	# 遍歷健檢中心相關科別路徑（排除骨科）
	for dir_path in health_dirs:
		if not os.path.exists(dir_path):
			continue  # 如果路徑不存在，跳過

		doc_dirs = os.listdir(dir_path)

		for doc_filename in doc_dirs:
			if doc_filename.endswith('.txt') and doc_filename.endswith(f"{employee_id}.txt"):
				matched_file = doc_filename
				matched_dir = dir_path
				name_and_title = doc_filename.rsplit('_', 1)[0].split('_', 2)[-1]
				# 以空白為界，分離並取得姓名與職稱
				name_parts = name_and_title.split(' ')
				name = name_parts[0]
				job_title = name_parts[1] if len(name_parts) > 1 else ''

				# 提取科別名稱與英文名稱
				department = get_clean_department_name(dir_path)
				department_en = get_clean_department_en(dir_path)
				break

		if matched_file:
			break  # 找到檔案後跳出迴圈

	if not matched_file:
		raise Http404("找不到醫師介紹")

	with open(os.path.join(matched_dir, matched_file), 'r', encoding='utf-8') as f:
		content = f.read()

	# 將 def parse_doctor_txt(content) 這段函式引入，帶入拆解後的變數
	parsed = parse_doctor_txt(content)

	# 因醫師照片路徑不同，需先建立指定路徑變數 (放 render 內會因加上醫師網址無法取得照片)
	doc_img = parsed['image']
	webp_img = convert_doctor_image_to_webp(doc_img) if doc_img else ''
	og_img_path = f'/media/department/img/{doc_img}'
	og_image_url = f"{settings.SITE_DOMAIN}{og_img_path}"

	# === 取得全部醫師清單（用於側邊欄，僅健檢中心醫師） ===
	doctors = []
	for dir_path in health_dirs:
		if not os.path.exists(dir_path):
			continue

		doc_dirs = os.listdir(dir_path)

		for doc_filename in doc_dirs:
			if doc_filename.endswith('.txt') and "D000" in doc_filename:
				try:
					parts = doc_filename.rsplit('_', 1)
					emp_id = parts[1].replace('.txt', '')
					name_title = parts[0].split('_', 2)[-1]
					name_parts = name_title.split(' ')
					d_name = name_parts[0]
					d_title = name_parts[1] if len(name_parts) > 1 else ''
					d_department = get_clean_department_name(dir_path)  # 提取科別名稱並去掉前綴
					d_department_en = get_clean_department_en(dir_path)  # 提取英文科別名稱
					doctors.append({
						'employee_id': emp_id,
						'name': d_name,
						'job_title': d_title,
						'department': d_department,
						'department_en': d_department_en,  # 加入英文科別名稱
					})
				except Exception as e:
					print(f"醫師清單錯誤: {e}")
					continue

	# === 醫師「相關文章」、「影音專區」=== 
	related_articles = get_related_articles(employee_id)
	related_videos = get_related_video(employee_id)
	# 沒有 「相關文章」、「影音專區」，則不顯示區塊
	has_articles = bool(related_articles)
	has_videos = bool(related_videos)

	return render(request, 'specialty_health/h-doctor-profile.html', {
		'name_and_title': name_and_title,
		'name': name,
		'job_title': job_title,
		'department': department,  # 傳遞科別變數到模板
		'department_en': department_en,  # 傳遞英文科別變數到模板
		'employee_id': employee_id,
		'expertise': parsed['expertise'],
		'expertise_list': parsed['expertise_list'],
		'education': parsed['education'],
		'education_list': parsed['education_list'],
		'image': doc_img,
		'image_webp': webp_img,
		'og_image': og_image_url,
		'related_articles': related_articles,
		'related_videos': related_videos,
		'has_articles': has_articles,
		'has_videos': has_videos,
		'doctors': doctors,  # 側邊欄清單
		'ga_id': '',
		'gtm_id': ''
	})

def article_share_view(request, get_filename):
	"""
	建立文章獨立頁：由於 get_related_articles 已先處理 filename (縮短網址用) → filename='2018-04-20_HA00504'
	所以文章頁會讀取不到檔案 → article_path='C:\\Python\\media\\news_2\\2018-04-20_HA00504.txt'
	設計一段程式，用關鍵字(例.2018-04-20_HA00504.txt') 去搜尋到對應的檔案(完整檔名)
	full_filename = 'C002_^_80歲阿公治二十年膝痛 機器人手臂破壞少復原快_企劃室_2022-04-06_^_2018-03-30_HA00434.txt'
	"""
	key_filename = f'{get_filename}.txt'  # 例：2018-04-20_HA00504.txt
	for temp_f in os.listdir(article_dir):
		if key_filename in temp_f:
			full_filename = temp_f.replace('.txt', '')
			break # 找到後，就不用再繼續搜尋檔案了

	article_path = os.path.join(article_dir, f"{full_filename}.txt")

	if not os.path.exists(article_path):
		raise Http404("找不到文章")

	meta = parse_article_filename(full_filename)
	parsed = parse_article_txt(article_path)

	context = {
		'title': meta['title'],
		# 'category': meta['category'],
		'date': meta['pub_date'],
		'employee_id': meta['employee_id'],
		'blocks': parsed['blocks'],  # 使用 parse_article_txt() 並傳入 blocks 給模板
		'image': parsed['image'],
		'summary': parsed['summary'],
		'tags': extract_tags_from_blocks(parsed['blocks']),
		'og_image': f"{settings.SITE_DOMAIN}/media/news_2/img/{parsed['og_img']}",
	}
	return render(request, 'specialty_health/h-article-detail.html', context)


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 健檢專案 (treatment_list / treatment_article) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# =================== 後端處理 ===================
# 後:健檢專案-圖片轉 webp 格式
def convert_item_icon_image_to_webp(original_filename):
	"""
	專用：轉換「健檢專案-卡片縮圖」為 WebP
	儲存路徑：media/specialty_health/img/h-icon/thumb-webp
	壓縮品質：50%
	"""
	source_dir = os.path.join(health_item_dir, 'h-icon')
	target_dir = os.path.join(source_dir, 'thumb-webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=50)

def convert_item_article_image_to_webp(original_filename):
	"""
	專用：轉換「健檢專案-內文圖片」為 WebP
	儲存路徑：media/specialty_health/img/h-articles-img/img_webp_article
	壓縮品質：80%
	"""
	source_dir = os.path.join(health_item_dir, 'h-articles-img')
	target_dir = os.path.join(source_dir, 'img_webp_article')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

# 後:健檢專案文章頁-AJAX 載入側邊選單
@require_GET
def health_treatment_sidenav_api(request):
	'''「健檢專案文章頁-AJAX 載入側邊選單 / 可切換文章頁面」'''
	treatments = get_grouped_treatments()
	return JsonResponse({'treatments': treatments})


# =================== 前端模板 ===================
def health_treatment_list(request):
	'''建立「健檢專案」頁'''
	treatments = get_grouped_treatments()
			
	return render(request, 'specialty_health/h-item-list.html', {
		'treatments': treatments,
		'og_image': '',
		'ga_id': '', 
		'gtm_id': ''
	})

def health_treatment_article(request, url_name):
	'''「健檢專案-文章頁」'''
	ort_t_dirs = os.listdir(health_item_dir)  # ← 每次 request 重新取得
	matched_item_file = None
	# item_name = None

	for item_filename in ort_t_dirs:
		if item_filename.endswith('.txt') and item_filename.endswith(f"{url_name}.txt"):
			matched_item_file = item_filename
			item_name = item_filename.rsplit('_', 2)[1]
			break

	if not matched_item_file:
		raise Http404("找不到文章")

	# 引入 parse_article_txt 函式，解析 txt 內容
	item_path = os.path.join(health_item_dir, matched_item_file)
	item_parsed = parse_article_txt(item_path)

	# 幫下載區塊加上序號 (若有多個 PDF，從第 2 個檔案才開始顯示序號)
	download_blocks = [b for b in item_parsed['blocks'] if b['type'] == 'download']
	if len(download_blocks) > 1:
		for i, b in enumerate(download_blocks, 1):
			if i > 1:
				b['serial'] = i

	# --- 新增：取得同群組的子專案（用於頂部切換按鈕） ---
	grouped = get_grouped_treatments()
	siblings = []
	for group in grouped:
		if group['is_group']:
			if any(child['url_name'] == url_name for child in group['children']):
				# 找到該群組，過濾掉當前專案
				siblings = [child for child in group['children'] if child['url_name'] != url_name]
				break

	context = {
		'item_title': item_name, # 標題取自檔名
		'item_a_title': item_parsed['item_a_title'], # 標題取自 txt 內容
		'blocks': item_parsed['blocks'],
		'image': item_parsed['image'],
		'item_summary': item_parsed['summary'],
		'tags': extract_tags_from_blocks(item_parsed['blocks']),
		'siblings': siblings, # 傳遞兄弟專案
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_health/h-articles/h-icon/{item_parsed['og_img_item']}"
	}
	return render(request, 'specialty_health/h-item-article-detail.html', context)


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 最新消息 (health_news) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ==================== 後端處理 ====================
# 後: 最新消息 - 圖片轉 WebP
def convert_news_image_to_webp(original_filename):
	"""
	專用：轉換「最新消息-內文圖片」為 WebP
	儲存路徑：media/news_1/img/img_webp_news
	壓縮品質：80%
	"""
	source_dir = news_img_dir
	target_dir = os.path.join(source_dir, 'img_webp_news')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

# 後: 最新消息 - 支援 ajax 分頁
@require_GET
def health_news_api(request):
	"""後端 API - 支援最新消息 Ajax 分頁"""
	try:
		page = int(request.GET.get("page", 1))
		per_page = int(request.GET.get("per_page", 12))  # 每頁筆數，預設 10

		all_news = get_all_health_news()
		paginator = Paginator(all_news, per_page)
		page_obj = paginator.get_page(page)

		data = [{
			'title': n['title'],
			'date': n['date'].strftime('%Y-%m-%d'),
			'url': n['url']
		} for n in page_obj]

		return JsonResponse({
			'news': data,
			'current_page': page_obj.number,
			'num_pages': paginator.num_pages,
		})
	except Exception as e:
		import traceback; traceback.print_exc()
		return JsonResponse({'error': str(e)}, status=500)

# 後：共用邏輯-取得所有最新消息（已排序，for 頁面/API 使用/)
def get_all_health_news():
	"""共用邏輯：取得所有最新消息（已排序，for 頁面/API 使用） - 支援新檔名格式 N001_類別_標題_YYYY-MM-DD.txt"""
	news_items = []

	for fname in os.listdir(NEWS_DIR):
		if not fname.endswith('.txt') or '^' not in fname:
			continue
		try:
			body_part, key = fname.replace('.txt', '').split('^')
			sub_parts = body_part.split('_')
			# 期待格式：N001_類別_標題_YYYY-MM-DD（標題 可能含底線，取 parts[2] 作為主標）
			if len(sub_parts) < 4:
				continue

			title = sub_parts[2].strip()
			date_str = sub_parts[3].strip()
			pub_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")

			news_items.append({
				'title': title,
				'date': pub_date,
				'key': key,
				'url': f"/specialty_health/health-news/{key}/"
			})

		except Exception as e:
			print(f"[錯誤] 解析最新消息檔案失敗：{fname}：{e}")
			continue

	news_items.sort(key=lambda x: x['date'], reverse=True)
	return news_items


# ==================== 前端模板 ====================
def health_news_list_view(request):
	"""health-news.html 列表頁 (前端走 Ajax 載入)"""
	# 新檔名格式不需 append_crc32_to_filenames()
	return render(request, "specialty_health/h-health-news.html", {
		'og_image': '',
		# "meta_title": "",
		# "meta_summary": ""
	})

def health_news_detail_view(request, key):
	try:
		matched_file = None
		for filename in os.listdir(NEWS_DIR):
			if filename.endswith(f'^{key}.txt'):
				matched_file = os.path.join(NEWS_DIR, filename)
				break

		if not matched_file or not os.path.exists(matched_file):
			return render(request, 'specialty_health/h-news-detail.html', {
				'error': True,
				'message': '找不到該則消息內容'
			})

		parsed_data = parse_article_txt(matched_file)

		# ▼ 新增這段：從檔名中取得 title 與 date ▼
		file_basename = os.path.basename(matched_file).replace('.txt', '')
		body_part = file_basename.split('^')[0]
		sub_parts = body_part.split('_')

		title = sub_parts[2] if len(sub_parts) >= 3 else '未命名'
		date = sub_parts[3] if len(sub_parts) >= 4 else ''

		# 幫下載區塊加上序號 (若有多個 PDF，從第 2 個檔案才開始顯示序號)
		download_blocks = [b for b in parsed_data['blocks'] if b.get('type') == 'download']
		if len(download_blocks) > 1:
			for i, b in enumerate(download_blocks, 1):
				if i > 1:
					b['serial'] = i

		return render(request, 'specialty_health/h-news-detail.html', {
			'data': {
				**parsed_data,
				'title': title
			},
			'date': date,
			'og_image': '',
		})

	except Exception as e:
		traceback.print_exc()
		return render(request, 'specialty_health/h-news-detail.html', {
			'error': True,
			'message': '資料載入失敗，請稍後再試'
		})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 媒體報導 (ort_media) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ==================== 後端處理 ====================

# ==== 若單位有增刪醫師，要重啟程式，再刷新網頁 ====

# 後: 「媒體報導」、「影音專區」共用函式-可根據 doctor-list 從 .txt 取得的 employee_id，去同步「媒體報導」、「影音專區」顯示的醫師資料。例如：doctor-list 移除醫師.txt，「媒體報導」的文章自動消失！
def get_active_doctor_ids():
	"""
	應用：當 doctor-list 刪除對應醫師的 .txt，employee_id 不會出現在 doctor-list → 「媒體報導」、「影音專區」的文章也會自動消失！
	"""

	ids = []
	for doc_dirs in dirs: # 遍歷所有科別路徑
		if not os.path.exists(doc_dirs):
			continue  # 如果路徑不存在，跳過

		doc_dirs = os.listdir(doc_dirs) # 取得該科別下的所有檔案

		for doc_filename in doc_dirs:
			if doc_filename.endswith('.txt') and "D000" in doc_filename:
				try:
					emp_id = doc_filename.rsplit('_', 1)[-1].replace('.txt', '')
					ids.append(emp_id)
				except Exception as e:
					print(f"錯誤解析 {doc_filename}：{e}")
					continue
	return ids

def get_health_center_doctor_ids():
	"""
	取得健檢中心專用的醫師ID（排除骨科）
	應用：健檢中心的媒體報導、推薦文章等，不應包含骨科醫師
	"""
	health_dirs = [
		os.path.join(settings.MEDIA_ROOT, 'department', 'D000_4_婦兒科', '1_婦科_Gynecology'),
		os.path.join(settings.MEDIA_ROOT, 'department', 'D000_2_內科', '5_肝膽腸胃科_Gastroenterology'),
		os.path.join(settings.MEDIA_ROOT, 'department', 'D000_2_內科', '8_家醫科_FamilyMedicine'),
	]
	
	ids = []
	for doc_dir in health_dirs:
		if not os.path.exists(doc_dir):
			continue
		for doc_filename in os.listdir(doc_dir):
			if doc_filename.endswith('.txt') and "D000" in doc_filename:
				try:
					emp_id = doc_filename.rsplit('_', 1)[-1].replace('.txt', '')
					ids.append(emp_id)
				except Exception as e:
					print(f"錯誤解析 {doc_filename}：{e}")
					continue
	return ids

# 後: 媒體報導主頁 - AJAX 載入分頁 (只更新文章區塊，不重新刷頁)
@require_GET
def health_media_api(request):
	""" Ajax 回傳健檢中心醫師的所有文章（支援分頁）"""
	employee_ids = get_health_center_doctor_ids() # 健檢中心專用醫師ID（排除骨科）
	all_articles_meta = []

	for post_filename in os.listdir(article_dir):
		if not post_filename.endswith('.txt'):
			continue
		if not any(emp_id in post_filename for emp_id in employee_ids):
			continue # ← 非 doctor-list 中的醫師，略過

		parts = post_filename.split('_')
		if len(parts) < 8:
			continue

		try:
			pub_date = datetime.datetime.strptime(parts[6], "%Y-%m-%d")
		except ValueError:
			continue

		all_articles_meta.append({
			'filename': post_filename,
			'title': parts[2],
			'pub_date': pub_date,
			'parts': parts
		})

	all_articles_meta.sort(key=lambda x: x['pub_date'], reverse=True)
	paginator = Paginator(all_articles_meta, 8)
	page = int(request.GET.get("page", 1))
	page_obj = paginator.get_page(page)

	articles = []
	for item in page_obj.object_list:
		parts = item['parts']
		web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"
		path = os.path.join(article_dir, item['filename'])
		parsed = parse_article_txt(path, detail=False)

		articles.append({
			'title': item['title'],
			'pub_date': item['pub_date'].strftime('%Y-%m-%d'),
			'image': parsed['image'],
			'summary': parsed['summary'],
			'url': f"/specialty_health/articles/{web_url}"
		})

	return JsonResponse({
		'articles': articles,
		'current_page': page_obj.number,
		'total_pages': paginator.num_pages
	})


# ==================== 前端模板 ====================
def health_media(request):
	''' 媒體報導主頁 '''
	all_articles = []
	# 使用健檢中心專用函式取得醫師ID（排除骨科）
	employee_ids = get_health_center_doctor_ids()

	# Step 2：從 media/news_2 找出所有對應醫師的文章
	for post_filename in os.listdir(article_dir):
		if not post_filename.endswith('.txt'):
			continue

		# 若該文章不包含 any 在 doctor-list 的 employee_id，則略過
		if not any(emp_id in post_filename for emp_id in employee_ids):
			continue

		parts = post_filename.split('_')
		if len(parts) < 8:
			continue  # 檔名格式不完整就跳過

		title = parts[2]
		date = parts[6]

		try:
			pub_date = datetime.datetime.strptime(date, "%Y-%m-%d")
		except ValueError:
			continue

		web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"  # 文章連結用縮網址
		path = os.path.join(article_dir, post_filename)

		all_articles.append({
			'title': title,
			'pub_date': pub_date,
			'web_url': web_url,
			'path': path
		})

	# Step 3：依日期由新到舊排序，只排序一次
	all_articles.sort(key=lambda x: x['pub_date'], reverse=True)

	# Step 4：分頁處理，每頁 8 筆
	paginator = Paginator(all_articles, 8)
	page = request.GET.get('page', 1)
	page_obj = paginator.get_page(page)

	# Only parse files for the items in page_obj
	paginated_articles = []
	for item in page_obj.object_list:
		parsed = parse_article_txt(item['path'], detail=False)
		paginated_articles.append({
			'title': item['title'],
			'pub_date': item['pub_date'],
			'image': parsed['image'],
			'summary': parsed['summary'],
			'filename': item['web_url'],
		})
	page_obj.object_list = paginated_articles

	# SEO meta：以當前第一筆為代表
	meta_title = page_obj.object_list[0]['title'] if page_obj.object_list else "媒體報導"
	meta_summary = page_obj.object_list[0]['summary'] if page_obj.object_list else ""
	meta_image = page_obj.object_list[0]['image'] if page_obj.object_list else ""

	return render(request, "specialty_health/h-health-reports.html", {
		'page_obj': page_obj,
		'meta_title': meta_title,
		'meta_summary': meta_summary,
		'meta_image': meta_image,
		'og_image': '',
		'ga_id': '',
		'gtm_id': ''
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 影音專區 (health_film) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ==================== 後端處理 ====================

# ==== 若單位有增刪醫師，要重啟程式，再刷新網頁 ====

# 後: 影音專區 - 回傳健檢中心影音專區影片（支援 ajax 分頁）
@require_GET
def health_film_api(request):
	"""Ajax 回傳影音專區影片（同時掃描 video_dir 與 Films_Dir，video_dir 仍以 doctor-list 過濾）"""
	try:
		employee_ids = get_health_center_doctor_ids()
		all_videos = []

		# 同時掃描兩個資料夾：原本的 video_dir（有醫師過濾）與新增的 Films_Dir（不過濾）
		search_dirs = [video_dir, Films_Dir]

		for d in search_dirs:
			if not os.path.exists(d):
				continue

			for video_filename in os.listdir(d):
				if not video_filename.endswith('.txt'):
					continue

				# 對原本的 video_dir 保留以 employee_id 過濾的邏輯
				if d == video_dir and not any(emp_id in video_filename for emp_id in employee_ids):
					continue

				filepath = os.path.join(d, video_filename)
				with open(filepath, 'r', encoding='utf-8-sig') as f:
					lines = f.read().splitlines()

				video_data = {
					'title': '',
					'date': '',
					'doctor_id': '',
					'youtube_url': '',
					'youtube_image': ''
				}

				for line in lines:
					if line.startswith('<yh>'):
						full_title = line.replace('<yh>', '').strip()
						video_data['title'] = re.split(r'[／/]', full_title)[0].strip()
					elif line.startswith('<yd>'):
						video_data['date'] = line.replace('<yd>', '').strip()
					elif line.startswith('<dr>'):
						video_data['doctor_id'] = line.replace('<dr>', '').strip()
					elif line.startswith('<ytb>'):
						ytb_url = line.replace('<ytb>', '').strip()
						video_data['youtube_url'] = ytb_url

						# 嘗試從不同格式的 youtube url 取得影片 id
						ytb_id = ''
						# watch?v=...
						m = re.search(r'v=([^&\s]+)', ytb_url)
						if m:
							ytb_id = m.group(1)
						# embed/ID
						elif 'embed/' in ytb_url:
							ytb_id = ytb_url.split('embed/')[-1].split('?')[0]
						# youtu.be/ID 或其它最後段為 ID
						else:
							ytb_id = ytb_url.rstrip('/').split('/')[-1].split('?')[0]

						if ytb_id:
							video_data['youtube_image'] = f'https://img.youtube.com/vi/{ytb_id}/hqdefault.jpg'

				# 若檔案內沒提供標題，嘗試從檔名取得（例如：F003_加入「糖尿病共照網」 免費檢查好處多多.txt）
				if not video_data['title']:
					name = video_filename.replace('.txt', '')
					if '_' in name:
						video_data['title'] = name.split('_', 1)[1]
					else:
						video_data['title'] = name

				# 若沒有 youtube_image，但有 youtube_url，嘗試再以 regex 解析一次
				if not video_data['youtube_image'] and video_data['youtube_url']:
					u = video_data['youtube_url']
					m = re.search(r'(?:v=|embed/|youtu\.be/)([^&\s?/]+)', u)
					if m:
						ytb_id = m.group(1)
						video_data['youtube_image'] = f'https://img.youtube.com/vi/{ytb_id}/hqdefault.jpg'

				all_videos.append(video_data)

		# 若沒有影片，回傳提示
		if not all_videos:
			return JsonResponse({
				'videos': [],
				'current_page': 1,
				'total_pages': 0,
				'message': '目前暫無影音文章'
			})

		# 以 date 欄位排序（字串），空日期會排到後面
		all_videos.sort(key=lambda x: x.get('date', ''), reverse=True)

		# 分頁，每頁 8 筆（保持與原本一致）
		paginator = Paginator(all_videos, 8)
		page = int(request.GET.get("page", 1))
		page_obj = paginator.get_page(page)

		return JsonResponse({
			'videos': page_obj.object_list,
			'current_page': page_obj.number,
			'total_pages': paginator.num_pages
		})
	except Exception as e:
		traceback.print_exc()
		return JsonResponse({'error': str(e)}, status=500)


# ==================== 前端模板 ====================
def health_film(request):
	"""影音專區主頁，初始渲染不載入影片內容，由 AJAX 呼叫 health_film_api 動態載入；附帶回傳是否存在 Films_Dir 的簡單狀態供前端使用"""
	has_films_dir = os.path.exists(Films_Dir) and any(f.endswith('.txt') for f in os.listdir(Films_Dir))
	return render(request, "specialty_health/h-health-film.html", {
		'og_image': '',
		'ga_id': '',
		'gtm_id': '',
		'has_films_dir': has_films_dir
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 衛教園地 (health_health_edu) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ==================== 後端處理 ====================
# 後: 衛教園地 - 分組資料並進行排序 (取得的資料可給 health_edu_api 及 health_health_edu 使用)
def get_health_edu_items():
	"""取得衛教園地分組後的資料（list of (title, [images])）"""
	base_path = os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc', '1_外科_Surgery', '骨科_Orthopedic')
	image_files = [f for f in os.listdir(base_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

	grouped_images = defaultdict(list)
	for filename in image_files:
		parts = filename.split('_page')
		if len(parts) >= 2:
			title = parts[0]
			grouped_images[title].append(filename)

	# 排序每組圖片（根據 page-xxxx 序號）
	for title in grouped_images:
		grouped_images[title].sort(key=lambda name: int(name.split('page-')[-1].split('.')[0]))

	# 保持順序
	grouped_images = OrderedDict(sorted(grouped_images.items()))
	return list(grouped_images.items()), base_path

# 後: 衛教園地 - 支援 ajax 分頁
@require_GET
def health_edu_api(request):
	page = int(request.GET.get("page", 1))
	per_page = int(request.GET.get("per_page", 8))
	all_items, base_path = get_health_edu_items()
	paginator = Paginator(all_items, per_page)
	page_obj = paginator.get_page(page)
	media_url = settings.MEDIA_URL + 'health_edu/Doc/1_外科_Surgery/骨科_Orthopedic/'
	data = [{
		'title': title,
		'images': [media_url + img for img in images],
	} for title, images in page_obj]
	return JsonResponse({
		'items': data,
		'current_page': page_obj.number,
		'num_pages': paginator.num_pages,
	})


# ==================== 前端模板 ====================
def health_health_edu(request):
	all_items, base_path = get_health_edu_items()
	paginator = Paginator(all_items, 8)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	context = {
		'media_url': settings.MEDIA_URL + 'health_edu/Doc/1_外科_Surgery/骨科_Orthopedic/',
		'page_obj': page_obj,
		'og_image': '',
	}
	return render(request, 'specialty_health/h-health-edu.html', context)


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 安全下載 PDF 檔案 ■■■■■■■■■■■■■■■■■■■■■■■■■■
@require_GET
def view_pdf_file(request, download_type, filename):
	"""
	安全的 PDF 檔案瀏覽功能（直接在瀏覽器開啟）
	- download_type: 'item' (健檢專案) 或 'news' (最新消息)
	- filename: 檔案名稱（僅檔名，不含路徑）
	
	資安措施：
	1. 檔案名稱白名單驗證（僅允許安全字元）
	2. 路徑遍歷攻擊防護
	3. 僅允許 PDF 檔案類型
	4. 檔案必須存在於指定資料夾
	"""
	
	# === 資安檢查 1：檔名白名單驗證（防止路徑遍歷攻擊） ===
	import re
	if not re.match(r'^[\w\u4e00-\u9fa5\-\.]+$', filename):
		raise Http404("無效的檔案名稱")
	
	# === 資安檢查 2：防止路徑遍歷攻擊 ===
	if '..' in filename or '/' in filename or '\\' in filename:
		raise Http404("無效的檔案路徑")
	
	# === 資安檢查 3：僅允許 PDF 檔案 ===
	if not filename.lower().endswith('.pdf'):
		raise Http404("僅支援 PDF 檔案下載")
	
	# === 根據類型決定檔案路徑 ===
	if download_type == 'item':
		file_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_health', 'h-articles', 'item-pdfs')
	elif download_type == 'news':
		file_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_health', 'h-news', 'news-pdfs')
	else:
		raise Http404("無效的下載類型")
	
	# === 檔案完整路徑 ===
	file_path = os.path.join(file_dir, filename)
	
	# === 資安檢查 4：確保檔案在允許的目錄內（防止符號連結攻擊） ===
	real_path = os.path.realpath(file_path)
	real_dir = os.path.realpath(file_dir)
	if not real_path.startswith(real_dir):
		raise Http404("無效的檔案路徑")
	
	# === 資安檢查 5：檔案必須存在 ===
	if not os.path.exists(file_path) or not os.path.isfile(file_path):
		raise Http404("檔案不存在")
	
	# === 直接在瀏覽器開啟 PDF ===
	try:
		# 使用 FileResponse 安全下載
		response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
		
		# 直接使用原始檔名設定 Content-Disposition
		response['Content-Disposition'] = f'inline; filename="{filename}"'
			
		print(f"[檔案瀏覽] 使用者開啟：{filename}")
		return response
	except Exception as e:
		print(f"[錯誤] 開啟檔案失敗：{str(e)}")
		raise Http404("開啟失敗")