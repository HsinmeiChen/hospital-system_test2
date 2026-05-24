from django.conf import settings
from django.shortcuts import render, Http404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger #分頁功能套件，Django本身就有支援
from collections import defaultdict # 分群套件
from Pomelo_test.utils import convert_image_to_webp
from health_edu.views import MyPaginator, remove_duplicate_items, get_image_name, get_time_str
import os, datetime, pymssql, re, glob, calendar, time, smtplib, openpyxl

try:
	import oracledb
	try:
		# 從 settings 讀取 Oracle Client 路徑
		oracle_client_path = getattr(settings, 'ORACLE_CLIENT_PATH', None)
		
		if oracle_client_path:
			# 使用指定路徑啟用 Thick Mode
			oracledb.init_oracle_client(lib_dir=oracle_client_path)
			print(f"Oracle Thick Mode enabled with path: {oracle_client_path}")
		else:
			# 嘗試使用預設路徑啟用 Thick Mode
			oracledb.init_oracle_client()
			print("Oracle Thick Mode enabled with default path")
	except Exception as e:
		print(f"Failed to enable Thick Mode: {e}")
		print("Will attempt to use Thin Mode, but may encounter password verifier issues")
	
	import oracledb as cx_Oracle
except ImportError:
	cx_Oracle = None
	print("oracledb module not installed")
from django.views.decorators.http import require_GET
from collections import OrderedDict
from django.utils.html import escape
from functools import lru_cache # 加入 @lru_cache 快取，避免每次重新掃描目錄
from django.core.mail import EmailMessage # 發送信件用
from django.views.decorators.http import require_POST # 發送信件用
import random # 隨機選擇 5 筆文章
import zlib # 計算 CRC32 hash 值
import traceback # 除錯（debug） 或 記錄錯誤訊息（logging）

from django.contrib import messages # Django 內建訊息 (成功 / 失敗) 框架
from .forms import ContactForm, send_email_to_client
from Pomelo_test.decorators import ratelimit_captcha, ratelimit_form_submit, captcha_failure_limit
# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 資料庫設定 ■■■■■■■■■■■■■■■■■■■■■■■■■■
case_plsql_host = settings.CASE_PLSQL_HOST
case_plsql_db = settings.CASE_PLSQL_DB
case_plsql_user = settings.CASE_PLSQL_USER
case_plsql_pwd = settings.CASE_PLSQL_PWD


# HIS資料庫相關程式
class PLSQLAPI:
	@staticmethod
	def get_connection():
		return cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)

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

# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 共用檔案路徑 ■■■■■■■■■■■■■■■■■■■■■■■■■■

# 共用資料夾路徑：醫師-個人介紹
dir = os.path.join(settings.MEDIA_ROOT, 'department', 'D000_1_外科', '1_骨科_Orthopedic')

# 共用資料夾路徑：醫師-最新消息、相關文章、影音專區
NEWS_FOLDER = os.path.join(settings.MEDIA_ROOT, 'news_1')
article_dir = os.path.join(settings.MEDIA_ROOT, 'news_2')
video_dir = os.path.join(settings.MEDIA_ROOT, 'news_3')

# 共用資料夾路徑：醫師-相關文章 (壓縮後-縮圖用)
news_img_dir = os.path.join(settings.MEDIA_ROOT, 'news_1', 'img')
media_base_dir = os.path.join(settings.MEDIA_ROOT, 'news_2', 'img')

# 共用資料夾路徑：特色醫療-治療項目
special_base_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_medical')
ort_treat_dir = os.path.join(special_base_dir, 'ort', 'treat-articles')


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 處理 txt 檔產生 hash 值使用 ■■■■■■■■■■■■■■■■■■■■■■■■■■

# 基礎路徑（請依你實際的 Django BASE_DIR 設定調整）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_DIR = os.path.join(BASE_DIR, '..', '..', 'media', 'news_1')  # 根據實際結構調整




# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 共用函式 ■■■■■■■■■■■■■■■■■■■■■■■■■
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
			webp_path = convert_treat_article_image_to_webp(filename)
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
	elif 'news_1' in filepath:
		img_url = '/media/news_1/img'
	elif 'treat-articles-img' in filepath:
		img_url = '/media/specialty_medical/ort/treat-articles/treat-articles-img/img_webp_article'
	else:
		img_url = '/media'

	org_thumb_img= ""
	thumb_img = ""
	card_image = ""
	treat_a_title = ""
	original_image = ""
	article_image = ""
	news_image = ""
	treat_article_image = ""
	content_blocks = []
	summary = ""
	has_first_img = False

	for line in lines:
		line = line.strip()

		# (1) 處理縮圖
		if line.startswith('<thumb-img>'):
			org_thumb_img = line.replace('<thumb-img>', '').strip()
			# 治療項目縮圖 (轉 webp 格式)
			thumb_img = convert_treat_icon_image_to_webp(org_thumb_img)

		# (2) 處理主要圖片
		elif line.startswith('<img1>'):
			if not detail and has_first_img:
				continue
			original_image = line.replace('<img1>', '').strip() # 原圖.jpg
			
			# 依來源資料夾只跑對應功能轉換圖片 (轉 webp 格式)-避免處理任何有 <img1> 標籤時，都會同時觸發四個不同路徑的 WebP 圖片轉換
			if 'news_2' in filepath:
				# 「醫師-相關文章 / 媒體報導」
				card_image = convert_image_to_webp_separate_folder(original_image)				
				article_image = convert_article_image_to_webp(original_image)
			
			elif 'news_1' in filepath:
				# 「最新消息」文章內文圖片
				news_image = convert_news_image_to_webp(original_image)

			elif 'treat-articles' in filepath or 'treat-articles-img' in filepath:
				# 「治療項目」文章內文圖片
				treat_article_image = convert_treat_article_image_to_webp(original_image)
			
			has_first_img = True

			if detail:
				content_blocks.append({
					'type': 'img',
					'class': 'a-img',
					'src': card_image,
					'article_src': article_image,
					'news_src': news_image,
					'treat_article_src': treat_article_image
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
			treat_a_title = line.replace('<h01>', '').strip()

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

			if detail:
				text = render_custom_tags(text, img_url=img_url) # img_url-自動判斷資料夾來源；
			
			if not summary:
				summary = text[:50]

			if not detail:
				continue

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
		'og_img_treat': org_thumb_img,
		'og_img': original_image,
		'image': card_image,
		'treat_a_title': treat_a_title,
		'summary': summary,
		'blocks': content_blocks,
	}


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 首頁 (ort_main) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ======================= 後端處理 ======================
# 後:首頁「Banner」
def convert_banner_image_to_webp(original_filename):
	"""
	專用：轉換 Banner 圖片為 WebP
	儲存路徑：media/specialty_medical/ort/banner/webp
	壓縮品質：80%
	"""
	source_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_medical', 'ort', 'banner')
	target_dir = os.path.join(source_dir, 'banner-webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

def ort_banner_api(request):
	banner_dir = os.path.join(settings.MEDIA_ROOT, 'specialty_medical', 'ort', 'banner')
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
	"""首頁「影音專區」專用 API：取得最新 7 筆影片"""
	employee_ids = get_active_doctor_ids()
	all_videos = []

	for video_filename in os.listdir(video_dir):
		if not video_filename.endswith('.txt'):
			continue
		if not any(emp_id in video_filename for emp_id in employee_ids):
			continue

		filepath = os.path.join(video_dir, video_filename)
		with open(filepath, 'r', encoding='utf-8-sig') as f:
			lines = f.read().splitlines()

		video_data = {
			'title': '',
			'date': '',
			'youtube_url': '',
			'youtube_image': ''
		}

		for line in lines:
			if line.startswith('<yh>'):
				full_title = line.replace('<yh>', '').strip()
				video_data['title'] = re.split(r'[／/]', full_title)[0].strip()
			elif line.startswith('<yd>'):
				video_data['date'] = line.replace('<yd>', '').strip()
			elif line.startswith('<ytb>'):
				ytb_url = line.replace('<ytb>', '').strip()
				ytb_id = ytb_url.split('/')[-1]
				video_data['youtube_url'] = ytb_url
				video_data['youtube_image'] = f'https://img.youtube.com/vi/{ytb_id}/hqdefault.jpg'

		all_videos.append(video_data)

	# 按日期排序 & 取前 3 筆
	all_videos.sort(key=lambda x: x['date'], reverse=True)
	latest_videos = all_videos[:3]

	return JsonResponse({'videos': latest_videos})

# 後:首頁「媒體報導」
@require_GET
def ort_media_home_api(request):
	"""首頁「媒體報導」專用：只回傳最新前 3 筆媒體報導文章"""
	employee_ids = get_active_doctor_ids()
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

		web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"
		path = os.path.join(article_dir, post_filename)

		all_articles.append({
			'title': parts[2],
			'pub_date': pub_date,
			'pub_date_str': pub_date.strftime('%Y-%m-%d'),
			'path': path,
			'url': f"/specialty_medical/articles/{web_url}"
		})

	all_articles.sort(key=lambda x: x['pub_date'], reverse=True)
	latest_articles = []
	for item in all_articles[:3]:
		parsed = parse_article_txt(item['path'], detail=False)
		latest_articles.append({
			'title': item['title'],
			'pub_date': item['pub_date_str'],
			'image': parsed['image'],
			'summary': parsed['summary'],
			'url': item['url']
		})

	return JsonResponse({'articles': latest_articles})

# 後:首頁「聯繫我們」
@ratelimit_form_submit(max_requests=5, window=300, redirect_url='ort_send_mail')  # 5 分鐘內最多 5 次提交
@captcha_failure_limit(max_failures=5, lockout_time=300, redirect_url='ort_send_mail', captcha_field='captcha')  # 5 次驗證碼錯誤後鎖定 5 分鐘
def ort_send_mail(request):
	"""
	聯絡我們頁面 - 包含表單功能
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
				return render(request, "specialty_medical/orthopedics/ortz-contact.html", {
					"form": form,
					'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png",
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
					return redirect('ort_send_mail')
			except Exception as e:
				import logging
				logging.exception("send_mail failed in specialty_medical contact view")
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
			return render(request, "specialty_medical/orthopedics/ortz-contact.html", {
				"form": form,
				'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png",
			})
	else:
		# GET 請求：顯示空表單
		form = ContactForm()

	return render(request, "specialty_medical/orthopedics/ortz-contact.html", {
		"form": form,
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png",
	})


# ======================= 前端模板 ======================
def ort_main(request):
	treatments = []
	ort_t_dirs = os.listdir(ort_treat_dir)  # ← 每次 request 重新取得

	for treat_filename in ort_t_dirs:
		if treat_filename.endswith('.txt') and ("treat" in treat_filename):
			try:
				match = re.search(r'T(\d+)', treat_filename)
				order_num = int(match.group(1)) if match else 9999

				parts = treat_filename.rsplit('_', 3)
				treat_title = parts[2]
				url_name = parts[3].replace('.txt', '')

				treat_path = os.path.join(ort_treat_dir, treat_filename)
				treat_parsed = parse_article_txt(treat_path, detail=False)

				treatments.append({
					'title': treat_title,
					'url_name': url_name,
					'thumb_img': treat_parsed['thumb_img'],
					'order': order_num
				})
			except Exception as e:
				print(f"[首頁治療項目解析失敗] {treat_filename}：{e}")
				continue

	treatments.sort(key=lambda x: x['order'])
	return render(request, "specialty_medical/orthopedics/ortz-index.html", {
		'treatments': treatments,
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png"
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 關於我們 (ort_about) ■■■■■■■■■■■■■■■■■■■■■■■■■■
def ort_about(request):
	return render(request, "specialty_medical/orthopedics/about-us.html", {
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png"
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

# 後:醫師「個人介紹」- 側邊選單：其他醫師
@require_GET
def doctor_sidenav_api(request):
	'''
	後端程式處理：醫師「個人介紹」頁中「側邊選單」帶入其他醫師選項列表
	'''
	sidenav_doctors = []
	doc_dirs = os.listdir(dir)  # ← 每次 request 重新取得
	for doc_filename in doc_dirs:
		if doc_filename.endswith('.txt') and "D000" in doc_filename:
			try:
				parts = doc_filename.rsplit('_', 1)
				emp_id = parts[1].replace('.txt', '')
				name_title = parts[0].split('_', 2)[-1]
				name_parts = name_title.split(' ')
				name = name_parts[0]
				job_title = name_parts[1] if len(name_parts) > 1 else ''
				sidenav_doctors.append({
					'employee_id': emp_id,
					'name': name,
					'job_title': job_title,
				})
			except:
				continue
	return JsonResponse({'doctors': sidenav_doctors})

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
			'url': f"/specialty_medical/articles/{a['filename']}"
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
	employee_ids = get_active_doctor_ids()
	candidate_files = []

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

		candidate_files.append((post_filename, parts, pub_date))

	# 隨機挑選最多 5 筆
	sampled_files = random.sample(candidate_files, min(5, len(candidate_files)))

	random_articles = []
	for post_filename, parts, pub_date in sampled_files:
		web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"
		path = os.path.join(article_dir, post_filename)
		parsed = parse_article_txt(path, detail=False)

		random_articles.append({
			'title': parts[2],
			'pub_date': pub_date.strftime('%Y-%m-%d'),
			'image': parsed['image'],
			'summary': parsed['summary'],
			'url': f"/specialty_medical/articles/{web_url}",
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

def doctor_list(request):
	'''建立「醫師列表」頁'''
	doctors = []
	doc_dirs = os.listdir(dir)  # ← 每次 request 重新取得

	conn = None
	try:
		conn = PLSQLAPI.get_connection()
	except Exception as conn_err:
		print(f"Failed to establish Oracle connection in doctor_list: {conn_err}")

	try:
		for doc_filename in doc_dirs:
			if doc_filename.endswith('.txt') and ("D000" in doc_filename):
				try:
					parts = doc_filename.rsplit('_', 1)				
					employee_id = parts[1].replace('.txt', '')
					name_and_title = parts[0].split('_', 2)[-1]
					# 以空白為界，分離並取得姓名與職稱
					name_parts = name_and_title.split(' ')
					name = name_parts[0]
					job_title = name_parts[1] if len(name_parts) > 1 else ''

					with open(os.path.join(dir, doc_filename), 'r', encoding='utf-8') as f:
						parsed = parse_doctor_txt(f.read())

					# 讀取停休診日期時間
					stop_raw = PLSQLAPI.Search_Stop_Show_by_Dr(employee_id, connection=conn)
					# 「停休診日期時間」按月份分群組
					stop_grouped = group_stops_by_month(stop_raw) if stop_raw else {}
					# 醫師照轉 webp，若沒有則帶 parsed['image']
					webp_image = convert_doctor_image_to_webp(parsed['image']) if parsed['image'] else ''

					doctors.append({
						'employee_id': employee_id,
						'name_and_title': name_and_title,
						'name': name,
						'job_title': job_title,
						'expertise': parsed['expertise'],
						'image': parsed['image'],
						'image_webp': webp_image,
						'stop_info': stop_grouped,
					})
				except Exception as e:
					print(f"錯誤解析 {doc_filename}：{e}")
					continue
	finally:
		if conn:
			try:
				conn.close()
			except:
				pass

	return render(request, 'specialty_medical/orthopedics/doctor_list.html', {
		'doctors': doctors,
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png",
		# 若有特定頁面讀其他 GA / GTM 碼，再直接這邊設定 (預設值-context_processors.py)
		'ga_id': '', 
		'gtm_id': ''
	})

def doctor_profile(request, employee_id):
	'''「個人介紹」頁'''
	doc_dirs = os.listdir(dir)  # ← 每次 request 重新取得
	matched_file = None
	name = None
	name_and_title = None
	job_title = ""

	# === 取得目前這位醫師的個人檔案 ===
	for doc_filename in doc_dirs:
		if doc_filename.endswith('.txt') and doc_filename.endswith(f"{employee_id}.txt"):
			matched_file = doc_filename
			name_and_title = doc_filename.rsplit('_', 1)[0].split('_', 2)[-1]
			# 以空白為界，分離並取得姓名與職稱
			name_parts = name_and_title.split(' ')
			name = name_parts[0]
			job_title = name_parts[1] if len(name_parts) > 1 else ''
			break

	if not matched_file:
		raise Http404("找不到醫師介紹")

	with open(os.path.join(dir, matched_file), 'r', encoding='utf-8') as f:
		content = f.read()

	# 將 def parse_doctor_txt(content) 這段函式引入，帶入拆解後的變數
	parsed = parse_doctor_txt(content)

	# 因醫師照片路徑不同，需先建立指定路徑變數 (放 render 內會因加上醫師網址無法取得照片)
	doc_img = parsed['image']
	webp_img = convert_doctor_image_to_webp(doc_img) if doc_img else ''
	og_img_path = f'/media/department/img/{doc_img}'
	og_image_url = f"{settings.SITE_DOMAIN}{og_img_path}"

	# === 取得全部醫師清單（用於側邊欄） ===
	doctors = []
	for doc_filename in doc_dirs:
		if doc_filename.endswith('.txt') and "D000" in doc_filename:
			try:
				parts = doc_filename.rsplit('_', 1)
				emp_id = parts[1].replace('.txt', '')
				name_title = parts[0].split('_', 2)[-1]
				name_parts = name_title.split(' ')
				d_name = name_parts[0]
				d_title = name_parts[1] if len(name_parts) > 1 else ''
				doctors.append({
					'employee_id': emp_id,
					'name': d_name,
					'job_title': d_title,
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

	return render(request, 'specialty_medical/orthopedics/doctor-profile.html', {
		'name_and_title': name_and_title,
		'name': name,
		'job_title': job_title,
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
		'doctors': doctors, # 側邊欄清單
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
		'og_image': f"{settings.SITE_DOMAIN}/media/news_2/img/{parsed['og_img']}"
	}
	return render(request, 'specialty_medical/orthopedics/article_detail.html', context)


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 治療項目 (treatment_list / treatment_article) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# =================== 後端處理 ===================
# 後:治療項目-圖片轉 webp 格式
def convert_treat_icon_image_to_webp(original_filename):
	"""
	專用：轉換「治療項目-卡片縮圖」為 WebP
	儲存路徑：media/specialty_medical/ort/img/treat-icon/thumb-webp
	壓縮品質：50%
	"""
	source_dir = os.path.join(ort_treat_dir, 'treat-icon')
	target_dir = os.path.join(source_dir, 'thumb-webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=50)

def convert_treat_article_image_to_webp(original_filename):
	"""
	專用：轉換「治療項目-內文圖片」為 WebP
	儲存路徑：media/specialty_medical/ort/img/treat-articles-img/img_webp_article
	壓縮品質：80%
	"""
	source_dir = os.path.join(ort_treat_dir, 'treat-articles-img')
	target_dir = os.path.join(source_dir, 'img_webp_article')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

# 後:治療項目文章頁-AJAX 載入側邊選單
@require_GET
def treatment_sidenav_api(request):
	'''「治療項目文章頁-AJAX 載入側邊選單 / 可切換文章頁面」'''
	treatments = []
	ort_t_dirs = os.listdir(ort_treat_dir)  # ← 每次 request 重新取得(如果放在全域變數，只會在伺服器啟動時執行一次，之後異動檔案不會更新--因 ajaxao6)
	for treat_filename in ort_t_dirs:
		if treat_filename.endswith('.txt') and "treat" in treat_filename:
			try:
				parts = treat_filename.rsplit('_', 3)
				title = parts[2]
				url_name = parts[3].replace('.txt', '')
				treatments.append({
					'title': escape(title),
					'url_name': url_name
				})
			except Exception as e:
				continue
	return JsonResponse({'treatments': treatments})


# =================== 前端模板 ===================
def treatment_list(request):
	'''建立「治療項目」頁'''
	treatments = []
	ort_t_dirs = os.listdir(ort_treat_dir)  # ← 每次 request 重新取得

	for treat_filename in ort_t_dirs:
		if treat_filename.endswith('.txt') and ("treat" in treat_filename): # 例.T001_treat_髖關節置換_mako01.txt
			try:
				# 抓出 T001 裡面的數字 → 1
				match = re.search(r'T(\d+)', treat_filename)
				order_num = int(match.group(1)) if match else 9999  # 沒抓到就放後面

				parts = treat_filename.rsplit('_', 3) # 從右起切 2 次；parts = ['T001', 'treat', '髖關節置換', 'mako01.txt']
				treat_title = parts[2] # 選索引值位於 2；treat_title = "髖關節置換"
				url_name = parts[3].replace('.txt', '') # 選索引值位於 3；url_name = "mako01"

				# 共用 parse_article_txt 這個函式解析 txt 內容 (函式已有 with open，所以根據參數 filepath 提供檔案路徑)
				treat_path = os.path.join(ort_treat_dir, treat_filename)
				treat_parsed = parse_article_txt(treat_path, detail=False)

				treatments.append({
					'title': treat_title,
					'url_name': url_name,
					'thumb_img': treat_parsed['thumb_img'],
					'order': order_num  # 排序用的欄位
				})
			except Exception as e:
				print(f"錯誤解析 {treat_filename}：{e}")
				continue

	# 根據 'order' 由小到大排序
	treatments.sort(key=lambda x: x['order'])
			
	return render(request, 'specialty_medical/orthopedics/treatment_list.html', {
		'treatments': treatments,
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png",
		# 若有特定頁面讀其他 GA / GTM 碼，再直接這邊設定 (預設值-context_processors.py)
		'ga_id': '', 
		'gtm_id': ''
	})

def treatment_article(request, url_name):
	'''「治療項目文章頁」'''
	ort_t_dirs = os.listdir(ort_treat_dir)  # ← 每次 request 重新取得
	matched_treat_file = None
	# treat_name = None

	for treat_filename in ort_t_dirs:
		if treat_filename.endswith('.txt') and treat_filename.endswith(f"{url_name}.txt"):
			matched_treat_file = treat_filename
			treat_name = treat_filename.rsplit('_', 2)[1]
			break

	if not matched_treat_file:
		raise Http404("找不到文章")

	# 引入 parse_article_txt 函式，解析 txt 內容
	treat_path = os.path.join(ort_treat_dir, matched_treat_file)
	treat_parsed = parse_article_txt(treat_path)

	context = {
		'treat_title': treat_name, # 標題取自檔名
		'treat_a_title': treat_parsed['treat_a_title'], # 標題取自 txt 內容
		'blocks': treat_parsed['blocks'],
		'image': treat_parsed['image'],
		'treat_summary': treat_parsed['summary'],
		'tags': extract_tags_from_blocks(treat_parsed['blocks']),
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/treat-articles/treat-icon/{treat_parsed['og_img_treat']}"
	}
	return render(request, 'specialty_medical/orthopedics/treat-article-detail.html', context)


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 最新消息 (ort_news) ■■■■■■■■■■■■■■■■■■■■■■■■■■

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
	"""共用邏輯：取得所有最新消息（已排序，for 頁面/API 使用）"""
	news_items = []

	for fname in os.listdir(NEWS_FOLDER):
		if not fname.endswith('.txt') or '^' not in fname:
			continue
		try:
			body_part, key = fname.replace('.txt', '').split('^')
			sub_parts = body_part.split('_')
			if len(sub_parts) < 7:
				continue

			title = sub_parts[2].strip()
			date = sub_parts[6].strip()
			pub_date = datetime.datetime.strptime(date, "%Y-%m-%d")

			news_items.append({
				'title': title,
				'date': pub_date,
				'key': key,
				'url': f"/specialty_medical/health-news/{key}/"
			})

		except Exception as e:
			print(f"[錯誤] 解析最新消息檔案失敗：{fname}：{e}")
			continue

	news_items.sort(key=lambda x: x['date'], reverse=True)
	return news_items


# ==================== 前端模板 ====================
def health_news_list_view(request):
	"""health-news.html 列表頁 (前端走 Ajax 載入)"""
	return render(request, "specialty_medical/orthopedics/health-news.html", {
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png",
		# "meta_title": "",
		# "meta_summary": ""
	})

def health_news_detail_view(request, key):
	try:
		matched_file = None
		for filename in os.listdir(NEWS_FOLDER):
			if filename.endswith(f'^{key}.txt'):
				matched_file = os.path.join(NEWS_FOLDER, filename)
				break

		if not matched_file or not os.path.exists(matched_file):
			return render(request, 'specialty_medical/orthopedics/news_detail.html', {
				'error': True,
				'message': '找不到該則消息內容'
			})

		parsed_data = parse_article_txt(matched_file)

		# ▼ 新增這段：從檔名中取得 title 與 date ▼
		file_basename = os.path.basename(matched_file).replace('.txt', '')
		body_part = file_basename.split('^')[0]
		sub_parts = body_part.split('_')

		title = sub_parts[2] if len(sub_parts) >= 3 else '未命名'
		date = sub_parts[6] if len(sub_parts) >= 7 else ''

		return render(request, 'specialty_medical/orthopedics/news_detail.html', {
			'data': {
				**parsed_data,
				'title': title
			},
			'date': date
		})

	except Exception as e:
		traceback.print_exc()
		return render(request, 'specialty_medical/orthopedics/news_detail.html', {
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
	doc_dirs = os.listdir(dir)  # ← 每次 request 重新取得
	for doc_filename in doc_dirs:
		if doc_filename.endswith('.txt') and "D000" in doc_filename:
			try:
				emp_id = doc_filename.rsplit('_', 1)[-1].replace('.txt', '')
				ids.append(emp_id)
			except:
				continue
	return ids

# 後: 媒體報導主頁 - AJAX 載入分頁 (只更新文章區塊，不重新刷頁)
@require_GET
def ort_media_api(request):
	""" Ajax 回傳 doctor-list 中骨科醫師的所有文章（支援分頁）"""
	employee_ids = get_active_doctor_ids() # 快取有效醫師
	all_articles = []

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

		web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"
		path = os.path.join(article_dir, post_filename)

		all_articles.append({
			'title': parts[2],
			'pub_date': pub_date,
			'pub_date_str': pub_date.strftime('%Y-%m-%d'),
			'path': path,
			'url': f"/specialty_medical/articles/{web_url}"
		})

	all_articles.sort(key=lambda x: x['pub_date'], reverse=True)
	paginator = Paginator(all_articles, 8)
	page = int(request.GET.get("page", 1))
	page_obj = paginator.get_page(page)

	paginated_articles = []
	for item in page_obj.object_list:
		parsed = parse_article_txt(item['path'], detail=False)
		paginated_articles.append({
			'title': item['title'],
			'pub_date': item['pub_date_str'],
			'image': parsed['image'],
			'summary': parsed['summary'],
			'url': item['url']
		})

	return JsonResponse({
		'articles': paginated_articles,
		'current_page': page_obj.number,
		'total_pages': paginator.num_pages
	})


# ==================== 前端模板 ====================
def ort_media(request):
	''' 媒體報導主頁 '''
	all_articles = []
	employee_ids = []
	doc_dirs = os.listdir(dir)

	# Step 1：取得 doctor-list 中所有骨科醫師的 employee_id
	for doc_filename in doc_dirs:
		if doc_filename.endswith('.txt') and "D000" in doc_filename:
			try:
				emp_id = doc_filename.rsplit('_', 1)[-1].replace('.txt', '')
				employee_ids.append(emp_id)
			except:
				continue

	# Step 2：從 media/news_2 找出所有對應醫師的文章
	for post_filename in os.listdir(article_dir):
		if not post_filename.endswith('.txt'):
			continue

		matched = False
		for emp_id in employee_ids:
			if emp_id in post_filename:
				matched = True
				break

		if not matched:
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
			'filename': web_url,
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
			'filename': item['filename'],
		})
	page_obj.object_list = paginated_articles

	# SEO meta：以當前第一筆為代表
	meta_title = page_obj.object_list[0]['title'] if page_obj.object_list else "媒體報導"
	meta_summary = page_obj.object_list[0]['summary'] if page_obj.object_list else ""
	meta_image = page_obj.object_list[0]['image'] if page_obj.object_list else ""

	return render(request, "specialty_medical/orthopedics/health-reports.html", {
		'page_obj': page_obj,
		'meta_title': meta_title,
		'meta_summary': meta_summary,
		'meta_image': meta_image,
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png",
		'ga_id': '',
		'gtm_id': ''
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 影音專區 (health_film) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ==================== 後端處理 ====================

# ==== 若單位有增刪醫師，要重啟程式，再刷新網頁 ====

# 後: 影音專區 - 回傳骨科醫師影音專區影片（支援 ajax 分頁）
@require_GET
def health_film_api(request):
	"""Ajax 回傳骨科醫師影音專區影片（支援分頁）"""
	employee_ids = get_active_doctor_ids()  # 取 doctor-list 中的骨科醫師 employee_id
	all_videos = []

	# 掃描 /media/news_3
	for video_filename in os.listdir(video_dir):
		if not video_filename.endswith('.txt'):
			continue
		if not any(emp_id in video_filename for emp_id in employee_ids):
			continue  # 非骨科醫師略過

		filepath = os.path.join(video_dir, video_filename)
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
				youtube_url = line.replace('<ytb>', '').strip()
				youtube_id = youtube_url.split('/')[-1]
				video_data['youtube_url'] = youtube_url
				video_data['youtube_image'] = f'https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg'

		all_videos.append(video_data)

	# **如果沒有影片，直接回傳提示**
	if not all_videos:
		return JsonResponse({
			'videos': [],
			'current_page': 1,
			'total_pages': 0,
			'message': '目前暫無影音文章'
		})

	# 按日期排序
	all_videos.sort(key=lambda x: x['date'], reverse=True)

	# 分頁，每頁 8 筆
	paginator = Paginator(all_videos, 8)
	page = int(request.GET.get("page", 1))
	page_obj = paginator.get_page(page)

	return JsonResponse({
		'videos': page_obj.object_list,
		'current_page': page_obj.number,
		'total_pages': paginator.num_pages
	})


# ==================== 前端模板 ====================
def health_film(request):
	"""影音專區主頁，初始渲染不載入影片內容，由 AJAX 呼叫 health_film_api 動態載入"""
	return render(request, "specialty_medical/orthopedics/health-film.html", {
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png",
		'ga_id': '',
		'gtm_id': ''
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 衛教園地 (ort_health_edu) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ==================== 後端處理 ====================
# 後: 衛教園地 - 分組資料並進行排序 (取得的資料可給 health_edu_api 及 ort_health_edu 使用)
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
def ort_health_edu(request):
	_dir = os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc', '1_外科_Surgery', '骨科_Orthopedic')
	if not os.path.exists(_dir):
		context = {
			'showfile': '外科',
			'sub_item_chinese': '骨科',
			'sub_item_en': 'Orthopedic',
			'message_lists_cut': [],
			'contacts_2': None,
			'paginator_2': None,
			'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png"
		}
		return render(request, 'specialty_medical/orthopedics/health-edu.html', context)

	pic_lists = []
	message_lists = []
	data = os.listdir(_dir)

	i = 0
	for file in data:
		if ".jpg" in file.lower() and '_' in file:
			file_path = os.path.join(_dir, file)
			unix_time = os.path.getmtime(file_path)
			datetimeObj = datetime.datetime.fromtimestamp(unix_time)
			dateStr = datetimeObj.strftime('%Y-%m-%d')

			pic_lists.append(file.split("_"))
			pic_lists[i].insert(0, "D00" + str(i))
			pic_lists[i].append(file)
			pic_lists[i].append(dateStr)
			i += 1
	pic_lists.sort(key=get_image_name)

	for p in pic_lists:
		temp_arr = []
		for f in pic_lists:
			if get_image_name(p) in f[1]:
				temp_arr.append(f[3])
		import hashlib
		name_hash = hashlib.md5(get_image_name(p).encode('utf-8')).hexdigest()[:8]
		message_lists.append({
			"index": p[0],
			"name": get_image_name(p),
			"hash": name_hash,
			"arr": temp_arr,
			"time": get_time_str(p)
		})
	message_lists = remove_duplicate_items(message_lists, "name")
	message_lists.sort(key=lambda x: (x["time"], x["name"]), reverse=True)

	page_limit = 12
	paginator_2 = MyPaginator(message_lists, page_limit)
	page_2 = request.GET.get('page', 1)
	contacts_2 = paginator_2.page(page_2)

	message_lists_cut = contacts_2
	MEDIA_URL = settings.MEDIA_URL
	context = {
		'showfile': '外科',
		'sub_item_chinese': '骨科',
		'sub_item_en': 'Orthopedic',
		'message_lists_cut': message_lists_cut,
		'contacts_2': contacts_2,
		'paginator_2': paginator_2,
		'MEDIA_URL': MEDIA_URL,
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png"
	}
	return render(request, 'specialty_medical/orthopedics/health-edu.html', context)


def ort_health_edu_detail(request, title_name):
	_dir = os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc', '1_外科_Surgery', '骨科_Orthopedic')
	if not os.path.exists(_dir):
		return redirect('/specialty_medical/ort-health-edu/')

	# 尋找與傳入 hash 值相符的中文標題
	import hashlib
	real_title = None
	all_files = os.listdir(_dir)
	for file in all_files:
		if file.lower().endswith('.jpg') and '_' in file:
			prefix = file.split('_')[0]
			computed_hash = hashlib.md5(prefix.encode('utf-8')).hexdigest()[:8]
			if computed_hash == title_name:
				real_title = prefix
				break

	# 備案：若傳入的本來就是中文標題 (相容舊網址)
	if not real_title:
		for file in all_files:
			if file.lower().endswith('.jpg') and file.startswith(title_name + '_'):
				real_title = title_name
				break

	# 若皆找不到，導回列表頁
	if not real_title:
		return redirect('/specialty_medical/ort-health-edu/')

	jpg_files = []
	for file in all_files:
		if file.lower().endswith('.jpg') and file.startswith(real_title + '_'):
			jpg_files.append(file)

	# 按照 page 序號排序
	def get_suffix_num(filename):
		parts = filename.split("_")
		if len(parts) > 1:
			suffix = os.path.splitext(parts[1])[0] # e.g. "page-0001"
			nums = re.findall(r'\d+', suffix)
			if nums:
				return int(nums[0])
		return 9999

	jpg_files.sort(key=get_suffix_num)

	# 進行 webp 轉換並將連結加入
	_webp_dir = os.path.join(_dir, 'webp')
	os.makedirs(_webp_dir, exist_ok=True)

	image_list = []
	for file in jpg_files:
		jpg_path = os.path.join(_dir, file)
		base_name = os.path.splitext(file)[0]
		webp_name = base_name + '.webp'
		webp_path = os.path.join(_webp_dir, webp_name)

		# 進行轉換
		has_webp = True
		if not os.path.exists(webp_path):
			try:
				from PIL import Image
				with Image.open(jpg_path) as img:
					img.save(webp_path, 'WEBP', quality=85)
			except Exception as e:
				has_webp = False

		MEDIA_URL = settings.MEDIA_URL
		jpg_url = f"{MEDIA_URL}health_edu/Doc/1_外科_Surgery/骨科_Orthopedic/{file}"
		if has_webp:
			webp_url = f"{MEDIA_URL}health_edu/Doc/1_外科_Surgery/骨科_Orthopedic/webp/{webp_name}"
		else:
			webp_url = jpg_url

		image_list.append({
			'jpg_url': jpg_url,
			'webp_url': webp_url,
			'has_webp': has_webp
		})

	return render(request, "specialty_medical/orthopedics/health-edu-detail.html", {
		'showfile': '外科',
		'sub_item_chinese': '骨科',
		'sub_item_en': 'Orthopedic',
		'title_name': real_title,
		'image_list': image_list,
		'MEDIA_URL': MEDIA_URL,
		'og_image': f"{settings.SITE_DOMAIN}/media/specialty_medical/ort/everan2.png"
	})