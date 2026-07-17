# 取得專案 (setting.py) 內的變數跟設定
from django.conf import settings

# 網頁渲染至 HTML, 例外類型用來找不到資源時，丟出 404 頁面, 重導向 (302、303)，常用於 POST 成功後的 PRG（避免重複提交）
from django.shortcuts import render, Http404, redirect

# 回傳不同類型的 HTTP 回應
from django.http import JsonResponse, HttpResponse, FileResponse

# 用於分頁並處理例外情況
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger

# 用於分群或累加資料 / 用於需要穩定排序的回傳資料
from collections import defaultdict, OrderedDict

# 用於轉義 HTML 字元，避免 XSS 攻擊
from django.utils.html import escape

# 限制只能用 GET 方法存取的裝飾器
from django.views.decorators.http import require_GET

# 用於快取資料，減少磁碟 I/O
from django.core.cache import cache

# 用來處理 URL 中的特殊字元，讓網址能正確顯示中文或其他特殊字符
import urllib.parse

# 用於掃描資料夾與讀取 txt 檔 / 連接 Oracle 資料庫 / 處理日期時間 / 解析檔名、從文字抽出影片 id 或標籤
import os, oracledb, datetime, re, time, hashlib, traceback

# 用於生成隨機驗證碼字元
import random

# Django 內建訊息 (成功 / 失敗) 框架
from django.contrib import messages

# 表單與郵件處理：匯入 ContactForm 驗證使用者輸入，以及 send_email_to_client 處理郵件發送邏輯
from .forms import ContactForm, send_email_to_client

# 自定義裝飾器：用於限制驗證碼請求與表單提交的頻率，防止惡意嘗試
from Pomelo_test.decorators import ratelimit_captcha, ratelimit_form_submit, captcha_failure_limit

# 自定義工具函式：用於檔案名稱附加雜湊值(快取控制)、產生驗證碼圖片、以及圖片格式轉換(WebP)
from Pomelo_test.utils import append_hash_to_filenames, generate_captcha_image_bytes, convert_image_to_webp


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 資料庫設定 ■■■■■■■■■■■■■■■■■■■■■■■■■■
case_plsql_host = settings.CASE_PLSQL_HOST
case_plsql_db = settings.CASE_PLSQL_DB
case_plsql_user = settings.CASE_PLSQL_USER
case_plsql_pwd = settings.CASE_PLSQL_PWD


# HIS資料庫相關程式
class PLSQLAPI:
	def Search_Stop_Show(date):
		try:
			connection = oracledb.connect(user=case_plsql_user, password=case_plsql_pwd, dsn=f"{case_plsql_host}/{case_plsql_db}")
		except Exception as e:
			print(f"Oracle connection failed in Search_Stop_Show: {e}")
			return []
		try:
			sql = '''SELECT SEC_SENAME,EMP_EMPNAME,SUBSTR(SCD_VISITDT,7,8),SCD_SHIFTNO,SCD_ROOMNO FROM REGSCD
			INNER JOIN BASEMP
				ON SCD_EMPNO = EMP_EMPNO 
			INNER JOIN BASSECT
				ON SCD_SECTNO = SEC_SECTNO
			WHERE SCD_CANCEL = 'Q'
				AND SCD_VISITDT LIKE :date
				AND EMP_DC = 'N'
			ORDER BY SCD_VISITDT,SCD_SHIFTNO'''
			c = connection.cursor()
			c.execute(sql, {'date': date + '%'})
			rows = c.fetchall()
			c.close()
			connection.close()
			return rows
		except Exception as e:
			print(f"SQL execution failed in Search_Stop_Show: {e}")
			try:
				c.close()
			except Exception:
				pass
			try:
				connection.close()
			except Exception:
				pass
			return []

	def get_connection():
		try:
			return oracledb.connect(user=case_plsql_user, password=case_plsql_pwd, dsn=f"{case_plsql_host}/{case_plsql_db}")
		except Exception as e:
			print(f"Oracle connection failed: {e}")
			return None

	def Search_Stop_Show_by_Dr(emp_id, sectno=None, connection=None): # ---【 Modify-多綁定科別 】---
		is_shared = (connection is not None)
		if not is_shared:
			try:
				connection = oracledb.connect(user=case_plsql_user, password=case_plsql_pwd, dsn=f"{case_plsql_host}/{case_plsql_db}")
			except Exception as e:
				print(f"Oracle connection failed in Search_Stop_Show_by_Dr: {e}")
				return []
		today = datetime.datetime.now()
		n_date = today.strftime("%Y%m%d")
		e_date = (today + datetime.timedelta(days=60)).strftime("%Y%m%d")
		try:
			# ---【 Modify-根據是否有傳入 sectno 決定 SQL 條件 】Start 至 REGSCD End ---
			# ---【 ADD-多綁科別-{sectno_cond}】
			if sectno and str(sectno).strip():
				sectno_cond = "AND SCD_SECTNO = :sectno"
			else:
				sectno_cond = "AND SCD_SECTNO = 'AB'"

			sql = f'''SELECT SEC_SENAME,EMP_EMPNAME,SCD_VISITDT,SCD_SHIFTNO,SCD_ROOMNO FROM REGSCD 
			INNER JOIN BASEMP
				ON SCD_EMPNO = EMP_EMPNO 
			INNER JOIN BASSECT
				ON SCD_SECTNO = SEC_SECTNO
			WHERE SCD_CANCEL = 'Q'
				AND SCD_EMPNO = :emp_id
				{sectno_cond}
				AND SCD_VISITDT BETWEEN :n_date AND :e_date
				AND EMP_DC = 'N'
			ORDER BY SCD_VISITDT'''
			c = connection.cursor()
			# ---【 ADD-動態參數綁定：若前端有傳入 sectno 才加入字典，避免 SQL 報錯 Start 】---
			params = {'emp_id': emp_id, 'n_date': n_date, 'e_date': e_date}
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
			if not is_shared:
				connection.close()
			return datas
		except Exception as e:
			print(f"SQL execution failed in Search_Stop_Show_by_Dr: {e}")
			try:
				c.close()
			except Exception:
				pass
			if not is_shared:
				try:
					connection.close()
				except Exception:
					pass
			return []



# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 共用檔案路徑 ■■■■■■■■■■■■■■■■■■■■■■■■■■
# 連動官網：醫師-個人介紹
dir = os.path.join(settings.MEDIA_ROOT, 'department', 'D000_2_內科', '1_心臟血管內科_CardiovascularMedicine')

# 連動官網：醫師-最新消息、媒體文章、影音專區
NEWS_FOLDER = os.path.join(settings.MEDIA_ROOT, 'news_1')
article_dir = os.path.join(settings.MEDIA_ROOT, 'news_2')
video_dir = os.path.join(settings.MEDIA_ROOT, 'news_3')

# 連動官網：醫師-相關媒體文章 (壓縮後-縮圖用)
news_img_dir = os.path.join(settings.MEDIA_ROOT, 'news_1', 'img')
media_base_dir = os.path.join(settings.MEDIA_ROOT, 'news_2', 'img')

# 專網：主資料夾
special_base_dir = os.path.join(settings.MEDIA_ROOT, 'cardio_center')

# 專網：治療文章
treat_dir = os.path.join(special_base_dir, 'cardio_treat_articles')

# 專網：影音專區
Films_Dir = os.path.join(special_base_dir, 'cardio_films')


# ■■■■■■■■■■■■■■■ (後) txt 檔：新增 hash 值 (CRC32)，為網址 slug 使用 ■■■■■■■■■■■■■■■
NEWS_DIR = os.path.join(settings.MEDIA_ROOT, 'news_1')
EDU_DIR = os.path.join(settings.MEDIA_ROOT, 'cardio_center', 'cardio_edu')

def append_crc32_to_filenames():
	append_hash_to_filenames(NEWS_DIR, extension='.txt', separator='^')
	append_hash_to_filenames(EDU_DIR, extension='.txt', separator='^')
	append_hash_to_filenames(video_dir, extension='.txt', separator='^')
	append_hash_to_filenames(Films_Dir, extension='.txt', separator='^')


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ (後) txt 檔：圖片轉 webp 格式 ■■■■■■■■■■■■■■■■■■■■■■■■■■
def convert_banner_image_to_webp(original_filename):
	"""
	專用：轉換【首頁-Banner】圖片為 WebP
	儲存路徑：media/cardio_center/cardio_banner/banner_webp
	壓縮品質：80%
	"""
	source_dir = os.path.join(settings.MEDIA_ROOT, 'cardio_center', 'cardio_banner')
	target_dir = os.path.join(source_dir, 'banner_webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

def convert_article_icon_image_to_webp(original_filename):
	"""
	專用：轉換「醫師相關媒體文章-卡片縮圖」為 WebP
	儲存路徑：media/news_2/img/thumb_webp
	壓縮品質：50%
	"""
	source_dir = media_base_dir
	target_dir = os.path.join(source_dir, 'thumb_webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=50)

def convert_article_image_to_webp(original_filename):
	"""
	專用：轉換「醫師相關媒體文章-內文圖片」為 WebP
	儲存路徑：media/news_2/img/img_webp_article
	壓縮品質：80%
	"""
	source_dir = media_base_dir
	target_dir = os.path.join(source_dir, 'img_webp_article')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

def convert_doctor_image_to_webp(original_filename):
	"""
	專用：轉換「醫師個人介紹-個人照」為 WebP
	儲存路徑：media/department/img/webp
	壓縮品質：80%
	"""
	source_dir = os.path.join(settings.MEDIA_ROOT, 'department', 'img')
	target_dir = os.path.join(source_dir, 'doc-webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

def convert_news_image_to_webp(original_filename):
	"""
	專用：轉換「最新消息-內文圖片」為 WebP
	儲存路徑：media/news_1/img/img_webp_news
	壓縮品質：80%
	"""
	source_dir = news_img_dir
	target_dir = os.path.join(source_dir, 'img_webp_news')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

def convert_treat_icon_image_to_webp(original_filename):
	"""
	專用：轉換「治療項目-卡片縮圖」為 WebP
	儲存路徑：media/cardio_center/cardio_treat_articles/treat_icon/thumb_webp
	壓縮品質：50%
	"""
	source_dir = os.path.join(treat_dir, 'treat_icon')
	target_dir = os.path.join(source_dir, 'thumb_webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=50)

def convert_treat_article_image_to_webp(original_filename):
	"""
	專用：轉換「治療項目-內文圖片」為 WebP
	儲存路徑：media/cardio_center/treat_articles/treat_articles_img/img_webp_article
	壓縮品質：80%
	"""
	source_dir = os.path.join(treat_dir, 'treat_articles_img')
	target_dir = os.path.join(source_dir, 'img_webp_article')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

def convert_edu_icon_image_to_webp(original_filename):
	"""
	專用：轉換「衛教園地-卡片縮圖」為 WebP
	儲存路徑：media/cardio_center/cardio_edu/edu_icon/thumb_webp
	壓縮品質：50%
	"""
	source_dir = os.path.join(settings.MEDIA_ROOT, 'cardio_center', 'cardio_edu', 'edu_icon')
	target_dir = os.path.join(source_dir, 'thumb_webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=50)

def convert_edu_article_image_to_webp(original_filename):  # 目前沒有使用，待測試
	"""
	專用：轉換「衛教園地-內文圖片」為 WebP
	儲存路徑：media/cardio_center/cardio_edu/edu_article/article_webp
	壓縮品質：80%
	"""
	source_dir = os.path.join(settings.MEDIA_ROOT, 'cardio_center', 'cardio_edu', 'edu_article')
	target_dir = os.path.join(source_dir, 'article_webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ (後) txt 檔：拆解檔案內容的標籤，轉成 html、套用 css ■■■■■■■■■■■■■■■■■■■■■■■■■■
def parse_article_txt(filepath, detail=True):
	'''
	將 txt 裡面的標籤進行拆解處理，讓之後其他程式讀取檔案進來時，加入這段函式，就可以依照各個標籤設置不同 css
	目前用於：醫師「相關文章-卡片項目、文章獨立頁內容」、媒體報導、最新消息、治療項目
	'''
	with open(filepath, 'r', encoding='utf-8-sig') as f:
		lines = f.readlines()

	# --- 1. 初始化圖片路徑與變數 (避免未定義錯誤) ---
	if 'news_2' in filepath:
		img_url = '/media/news_2/img'
	elif 'news_1' in filepath:
		img_url = '/media/news_1/img'
	elif 'treat_articles_img' in filepath:
		img_url = '/media/cardio_center/cardio_treat_articles/treat_articles_img/img_webp_article'
	elif 'cardio_edu' in filepath:
		img_url = '/media/cardio_center/cardio_edu/edu_article/'
	else:
		img_url = '/media'

	org_thumb_img = thumb_img = card_image = article_title = original_image = ""
	article_image = news_image = treat_article_image = edu_article_image = summary = ""
	content_blocks = []
	has_first_img = False

	# --- 定義簡單標籤字典 (將相似格式的標籤集中管理，避免寫一堆 elif) ---
	SIMPLE_TAGS = {
		'<cap>':   {'type': 'h3', 'semantic': 'section_title', 'class': 'title-02'},
		'<li-t>':  {'type': 'h4', 'semantic': 'sub_title', 'class': 'list-title'},		
		'<quo>':   {'type': 'blockquote', 'semantic': 'quote', 'class': 'quote-box'},
		'<li-p>':  {'type': 'li', 'semantic': 'keypoint', 'class': 'list-text'},
		'<li-o>':  {'type': 'li', 'semantic': 'ordered_keypoint', 'class': 'list-num'},
		'<li-q>':  {'type': 'h4', 'semantic': 'faq_question', 'class': 'list-question'},
		'<li-a>':  {'type': 'div', 'semantic': 'faq_answer', 'class': 'list-answer'},
		'<t-note>':{'type': 'div', 'class': 'text-note'},
	}

	for line in lines:
		line = line.strip()
		if not line: continue

		# --- 2. 處理縮圖 (<thumb-img>) ---
		if line.startswith('<thumb-img>'):
			org_thumb_img = line.replace('<thumb-img>', '').strip()
			if 'cardio_edu' in filepath:
				thumb_img = convert_edu_icon_image_to_webp(org_thumb_img)
			else:
				thumb_img = convert_treat_icon_image_to_webp(org_thumb_img)

		# --- 3. 處理文章主圖片 (<img1>) ---
		elif line.startswith('<img1>'):
			if not detail and has_first_img: continue
			original_image = line.replace('<img1>', '').strip() # 原圖.jpg
			has_first_img = True
			
			if 'news_2' in filepath:
				card_image = convert_article_icon_image_to_webp(original_image)				
				article_image = convert_article_image_to_webp(original_image)
			elif 'news_1' in filepath:
				news_image = convert_news_image_to_webp(original_image)
			elif 'treat_articles' in filepath or 'treat_articles_img' in filepath:
				treat_article_image = convert_treat_article_image_to_webp(original_image)
			elif 'cardio_edu' in filepath:
				edu_article_image = convert_edu_article_image_to_webp(original_image)
			
			if detail:
				content_blocks.append({
					'type': 'img',
					'semantic': 'image',
					'original_image': original_image,
					# 'class': 'a-img',
					'src': card_image,
					'article_src': article_image,
					'news_src': news_image,
					'treat_article_src': treat_article_image,
					'edu_article_src': edu_article_image
				})

		# --- 4. 處理大標題 (<h01>) 與 發布日期 (<posted>) ---
		elif line.startswith(('<h01>', '<h>')):
			article_title = line.replace('<h01>', '').replace('<h>', '').strip()
		
		elif line.startswith('<posted>'):
			if detail: content_blocks.append({'type': 'div', 'class': 'posted-date', 'text': line.replace('<posted>', '').strip()})

		# --- 5. 處理獨立影片 (<yt>) ---
		elif line.startswith('<yt>'):
			if detail:
				yt_url = line.replace('<yt>', '').strip()
				iframe_html = f'<iframe class="embed-responsive-item" src="{yt_url}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen loading="lazy"></iframe>'			
				content_blocks.append({'type': 'video', 'semantic': 'video', 'class': 'embed-responsive embed-responsive-16by9', 'text': iframe_html})

		# --- 6. 處理一般段落 (<t>)，並解析段落中內嵌的圖片或影片 ---
		elif line.startswith('<t>'):
			if 'news_2' in filepath and '<a href' in line and '預約掛號' in line:
				continue # 過濾特定預約掛號文字

			text = line.replace('<t>', '').strip()
			
			if detail:
				# 替換內嵌的 <img1>
				if '<img1>' in text:
					parts = text.split('<img1>')
					for part in parts[1:]:
						filename = part.strip().split()[0].split('</')[0]
						
						if 'cardio_edu' in filepath:
							webp_path = convert_edu_article_image_to_webp(filename)
						elif 'treat_articles_img' in filepath:
							webp_path = convert_treat_article_image_to_webp(filename)
						elif 'news_1' in filepath:
							webp_path = convert_news_image_to_webp(filename)
						else:
							webp_path = convert_article_image_to_webp(filename)

						img_tag = f'<img src="/media/{webp_path}" class="img-fluid w-100">' if webp_path else f'<img src="{img_url}/{filename}" class="img-fluid w-100">'
						text = text.replace(f'<img1>{filename}', img_tag)

				# 替換內嵌的 <yt>
				if '<yt>' in text:
					yt_url = text.replace('<yt>', '').strip()
					text = f'<div class="info_iframe"><iframe src="{yt_url}" frameborder="0" allowfullscreen sandbox="allow-same-origin allow-scripts"></iframe></div>'

			# 設定摘要 (前50字)
			if not summary: summary = text[:50]
			if not detail: continue

			# 若為新聞連結，設定按鈕樣式；否則為一般文字段落
			if text.startswith('新聞連結'):
				links = re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', text)
				link_html = "".join([f'<a href="{href}" class="btn btn-link" target="_blank">📰 {label}</a>' for href, label in links])
				content_blocks.append({'type': 'p', 'semantic': 'paragraph', 'class': 'news-links', 'text': link_html})
			else:
				content_blocks.append({'type': 'p', 'semantic': 'paragraph', 'class': 'a-paragraph', 'text': text})

		# --- 7. 透過字典比對，快速處理簡單格式的標籤 ---
		else:
			matched_tag = False
			for tag, config in SIMPLE_TAGS.items():
				if line.startswith(tag):
					if detail:
						block = config.copy()
						block['text'] = line.replace(tag, '').strip()
						content_blocks.append(block)
					matched_tag = True
					break
			if matched_tag: continue

	# --- 8. 迴圈結束：若不需要詳細內容 (detail=False)，只回傳摘要與圖片等中繼資料 ---
	if not detail:
		return {
			'thumb_img': thumb_img, 'og_img_treat': org_thumb_img, 'og_img': original_image,
			'image': card_image, 'article_title': article_title, 'summary': summary, 'blocks': []
		}

	# --- 9. 後處理：將連續的列表項目 (ul/ol) 合併成同一個群組，方便前端渲染 ---
	grouped_blocks = []
	current_list = None

	for block in content_blocks:
		sem = block.get('semantic')
		if sem in ['keypoint', 'ordered_keypoint']:
			if current_list and current_list['semantic'] == sem:
				current_list['items'].append(block)
			else:
				current_list = {'type': 'ol' if sem == 'ordered_keypoint' else 'ul', 'semantic': sem, 'items': [block], 'class': 'mb-0'}
				grouped_blocks.append(current_list)
		else:
			current_list = None
			grouped_blocks.append(block)

	return {
		'thumb_img': thumb_img, 'og_img_treat': org_thumb_img, 'og_img': original_image, 'image': card_image,
		'article_title': article_title, 'summary': summary, 'blocks': grouped_blocks
	}



# ■■■■■■■■■■■■■■■■■■■■■■■■■■ (後) 動態取得目前在職（或是還有個人介紹頁面）的醫師 emp_id ■■■■■■■■■■■■■■■■■■■■■■■■■■
def get_active_doctor_ids():
	"""
	# 當 doctor-list 移除對應醫師的 .txt 檔案後，
	# 該醫師的 employee_id 將不再出現在 doctor-list 中，
	# 因此「媒體報導」與「影音專區」會自動隱藏該醫師的所有文章。
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


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 專網首頁(main) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ▼▼▼▼▼▼▼▼▼▼ 後端處理 ▼▼▼▼▼▼▼▼▼▼
# ---未測試 banner_link.txt
def cardio_banner_api(request):
	''' 首頁：Banner API '''
	banner_dir = os.path.join(settings.MEDIA_ROOT, 'cardio_center', 'cardio_banner')
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

	# 讀取 banner_link.txt
	link_map = {}
	link_file = os.path.join(banner_dir, 'banner_link.txt')
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

@require_GET
def cardio_news_home_api(request):
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

@require_GET
def cardio_film_home_api(request):
	"""首頁「影音專區」專用 API：取得分類與過濾後的影音"""
	employee_ids = get_active_doctor_ids()
	left_candidates = []
	right_candidates = []

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
				'youtube_image': '',
				'index_val': '',
				'youtube_id': ''
			}

			# 解析檔名索引值 (C003_xxx_2_xxx.txt)
			name = video_filename.replace('.txt', '')
			parts = name.split('_')
			if len(parts) >= 3:
				video_data['index_val'] = parts[2].strip()

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
						m = re.search(r'v=([^&]+)', ytb_url)
						if m:
							ytb_id = m.group(1)
					elif 'embed/' in ytb_url:
						ytb_id = ytb_url.split('embed/')[-1].split('?')[0]
					else:
						ytb_id = ytb_url.rstrip('/').split('/')[-1].split('?')[0]

					if ytb_id:
						video_data['youtube_id'] = ytb_id
						video_data['youtube_image'] = f'https://img.youtube.com/vi/{ytb_id}/maxresdefault.jpg'

			# 若檔案內沒提供標題，嘗試從檔名取得
			if not video_data['title']:
				if '_' in name:
					video_data['title'] = name.split('_', 1)[1]
				else:
					video_data['title'] = name

			# 根據索引值分類
			if video_data['index_val'] == '2':
				left_candidates.append(video_data)
			elif video_data['index_val'] in ['4', '1']:
				right_candidates.append(video_data)

	# 按 date 降序排列
	left_candidates.sort(key=lambda x: x.get('date', ''), reverse=True)
	right_candidates.sort(key=lambda x: x.get('date', ''), reverse=True)

	# 取左側 1 個最新影音，右側 1 個最新影音
	left_video = left_candidates[0] if left_candidates else None
	right_videos = right_candidates[:1]

	latest_videos = []
	if left_video:
		latest_videos.append(left_video)
	latest_videos.extend(right_videos)

	return JsonResponse({'videos': latest_videos})

@require_GET
def cardio_media_home_api(request):
	"""首頁「媒體報導」專用：只回傳最新前 3 筆媒體報導文章"""
	employee_ids = get_active_doctor_ids()
	all_articles = []
	valid_files = []

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
			valid_files.append((pub_date, post_filename, parts))
		except ValueError:
			continue

	# Sort filenames by date descending
	valid_files.sort(key=lambda x: x[0], reverse=True)

	# Only parse the top 3!
	for pub_date, post_filename, parts in valid_files[:3]:
		web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"
		path = os.path.join(article_dir, post_filename)
		parsed = parse_article_txt(path, detail=False)

		all_articles.append({
			'filename_title': parts[2],
			'pub_date': pub_date.strftime('%Y-%m-%d'),
			'image': parsed['image'],
			'summary': parsed['summary'],
			'url': f"/cardio_center/articles/{web_url}"
		})

	return JsonResponse({'articles': all_articles})


# ▼▼▼▼▼▼▼▼▼▼ 前端處理 ▼▼▼▼▼▼▼▼▼▼
def cardio_main(request):
	# -----[首頁：治療項目]-----
	treatments = []
	cardio_t_dirs = os.listdir(treat_dir) if os.path.exists(treat_dir) else []  # ← 每次 request 重新取得

	for treat_filename in cardio_t_dirs:
		if treat_filename.endswith('.txt') and ("treat" in treat_filename):
			try:
				match = re.search(r'T(\d+)', treat_filename)
				order_num = int(match.group(1)) if match else 9999

				parts = treat_filename.rsplit('_', 3)
				filename_title = parts[2]
				url_name = parts[3].replace('.txt', '')

				treat_path = os.path.join(treat_dir, treat_filename)
				treat_parsed = parse_article_txt(treat_path, detail=False)

				treatments.append({
					'treat_title': filename_title,
					'url_name': url_name,
					'thumb_img': treat_parsed['thumb_img'],
					'summary': treat_parsed['summary'],
					'order': order_num
				})
			except Exception as e:
				print(f"[首頁-治療項目解析失敗] {treat_filename}：{e}")
				continue

	treatments.sort(key=lambda x: x['order'])

	# -----[首頁：媒體報導 (最新 5 筆)]-----
	media_layer1_1 = None
	media_layer1_2 = None
	media_layer2 = []
	try:
		employee_ids = get_active_doctor_ids()
		valid_files = []
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
				valid_files.append((pub_date, post_filename, parts))
			except ValueError:
				continue
		valid_files.sort(key=lambda x: x[0], reverse=True)
		media_articles = []
		for pub_date, post_filename, parts in valid_files[:5]:
			web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"
			path = os.path.join(article_dir, post_filename)
			parsed = parse_article_txt(path, detail=False)
			media_articles.append({
				'filename_title': parts[2],
				'pub_date': pub_date.strftime('%Y.%m.%d'),
				'image': parsed['image'],
				'summary': parsed['summary'],
				'url': f"/cardio_center/articles/{web_url}"
			})
		if len(media_articles) > 0:
			media_layer1_1 = media_articles[0]
		if len(media_articles) > 1:
			media_layer1_2 = media_articles[1]
		if len(media_articles) > 2:
			media_layer2 = media_articles[2:5]
	except Exception as e:
		print(f"[首頁-媒體報導解析失敗]：{e}")

	# -----[首頁：衛教園地 (隨機 3 筆)]-----
	random_edus = []
	try:
		all_items, base_path = get_health_edu_items()
		if all_items:
			chosen_items = random.sample(all_items, min(3, len(all_items)))
			for item in chosen_items:
				filename_title, title_hash, content, is_txt, thumb = item
				pub_date = ""
				summary = ""
				
				if is_txt:
					# content 為檔名，例如: E001_edu_xxx_2025-05-16^hash.txt
					image_url = settings.MEDIA_URL + thumb if thumb else ''
					name_part = content.split('^')[0]
					parts = name_part.split('_')
					if len(parts) >= 4:
						raw_date = parts[3]
						try:
							dt = datetime.datetime.strptime(raw_date, "%Y-%m-%d")
							pub_date = dt.strftime("%Y.%m.%d")
						except ValueError:
							pub_date = raw_date.replace('-', '.')
					
					try:
						edu_txt_dir = os.path.join(settings.MEDIA_ROOT, 'cardio_center', 'cardio_edu')
						filepath = os.path.join(edu_txt_dir, content)
						parsed = parse_article_txt(filepath, detail=False)
						summary = parsed.get('summary', '')
					except Exception as e:
						print(f"[首頁-衛教文章摘要解析失敗]：{e}")
				else:
					# 舊圖片組
					thumb_image = content[0] if content else ''
					image_url = f"{settings.MEDIA_URL}health_edu/Doc/0_內科_InternalMedicine/心臟血管內科_CardiovascularMedicine/{thumb_image}" if thumb_image else ''
					pub_date = "衛教分享"
					summary = "點擊瀏覽完整衛教圖文內容。"
				
				random_edus.append({
					'filename_title': filename_title,
					'image': image_url,
					'pub_date': pub_date,
					'summary': summary,
					'url': f"/cardio-center/edu/{title_hash}/"
				})
	except Exception as e:
		print(f"[首頁-衛教資訊隨機取得失敗]：{e}")

	# -----[首頁：回傳至前端]-----
	return render(request, "cardio_center/cardio_index.html", {
		'treatments': treatments,
		'og_image': '',
		'media_layer1_1': media_layer1_1,
		'media_layer1_2': media_layer1_2,
		'media_layer2': media_layer2,
		'random_edus': random_edus,
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 關於我們(about) ■■■■■■■■■■■■■■■■■■■■■■■■■■
def cardio_about(request):
	return render(request, "cardio_center/cardio_about.html", {   
		'og_image': "",
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 最新消息 (news) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ▼▼▼▼▼▼▼▼▼▼ 後端處理 ▼▼▼▼▼▼▼▼▼▼
def get_all_health_news():
	'''取得所有最新消息，已排序，for 頁面/API 使用'''
	news_items = []

	for fname in os.listdir(NEWS_FOLDER):
		if not fname.endswith('.txt') or '^' not in fname:
			continue
		try:
			body_part, key = fname.replace('.txt', '').split('^')
			sub_parts = body_part.split('_')
			if len(sub_parts) < 7:
				continue

			filename_title = sub_parts[2].strip()
			date = sub_parts[6].strip()
			pub_date = datetime.datetime.strptime(date, "%Y-%m-%d")

			news_items.append({
				'title': filename_title,
				'date': pub_date,
				'key': key,
				'url': f"/cardio-center/cardio-news/{key}/"
			})

		except Exception as e:
			print(f"[錯誤] 解析最新消息檔案失敗：{fname}：{e}")
			continue

	news_items.sort(key=lambda x: x['date'], reverse=True)
	return news_items

@require_GET
def cardio_news_api(request):
	"""後端 API - 支援最新消息 Ajax 分頁"""
	try:
		page = int(request.GET.get("page", 1))
		per_page = int(request.GET.get("per_page", 20))  # 每頁筆數，預設 20

		all_news = get_all_health_news()
		paginator = Paginator(all_news, per_page)
		page_obj = paginator.get_page(page)

		data = [{
			'title': n['filename_title'],
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


# ▼▼▼▼▼▼▼▼▼▼ 前端處理 ▼▼▼▼▼▼▼▼▼▼
def cardio_news_list_view(request):
	'''最新消息列表頁(前端走 Ajax 載入)'''
	return render(request, "cardio_center/cardio_news.html", {
		'og_image': '',
		# "meta_title": "",
		# "meta_summary": ""
	})

def cardio_news_detail_view(request, key):
	'''最新消息詳細內容頁'''
	try:
		matched_file = None
		for filename in os.listdir(NEWS_FOLDER):
			if filename.endswith(f'^{key}.txt'):
				matched_file = os.path.join(NEWS_FOLDER, filename)
				break

		if not matched_file or not os.path.exists(matched_file):
			return render(request, 'cardio_center/cardio_news_detail.html', {
				'error': True,
				'message': '找不到該則消息內容'
			})

		parsed_data = parse_article_txt(matched_file)

		# ▼ 從檔名中取得 title 與 date ▼
		file_basename = os.path.basename(matched_file).replace('.txt', '')
		body_part = file_basename.split('^')[0]
		sub_parts = body_part.split('_')

		filename_title = sub_parts[2] if len(sub_parts) >= 3 else '未命名'
		date = sub_parts[6] if len(sub_parts) >= 7 else ''

		return render(request, 'cardio_center/cardio_news_detail.html', {
			'data': {
				**parsed_data,
				'title': filename_title
			},
			'date': date
		})

	except Exception as e:
		traceback.print_exc()
		return render(request, 'cardio_center/cardio_news_detail.html', {
			'error': True,
			'message': '資料載入失敗，請稍後再試'
		})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 媒體報導 (media) ■■■■■■■■■■■■■■■■■■■■■■■■■■
# ▼▼▼▼▼▼▼▼▼▼ 後端處理 ▼▼▼▼▼▼▼▼▼▼
@require_GET
def cardio_media_api(request):
	""" Ajax 回傳 doctor-list 中相關科別醫師的所有文章（支援分頁-只更新文章區塊，不重新刷頁）"""
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
			'filename_title': parts[2],
			'pub_date': pub_date,
			'pub_date_str': pub_date.strftime('%Y-%m-%d'),
			'path': path,
			'url': f"/cardio-center/articles/{web_url}"
		})

	all_articles.sort(key=lambda x: x['pub_date'], reverse=True)
	paginator = Paginator(all_articles, 10)
	page = int(request.GET.get("page", 1))
	page_obj = paginator.get_page(page)

	paginated_articles = []
	for item in page_obj.object_list:
		parsed = parse_article_txt(item['path'], detail=False)
		paginated_articles.append({
			'title': item['filename_title'],
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

@require_GET
def random_cardio_reports_api(request):
	"""隨機取得 5 筆媒體報導文章（供 cardio-article-detail 側欄卡片用）"""
	employee_ids = get_active_doctor_ids()
	all_articles = []
	valid_files = []

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
			valid_files.append((pub_date, post_filename, parts))
		except ValueError:
			continue

	# Sample up to 5 files first
	sampled_files = random.sample(valid_files, min(5, len(valid_files)))

	for pub_date, post_filename, parts in sampled_files:
		web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"
		path = os.path.join(article_dir, post_filename)
		parsed = parse_article_txt(path, detail=False)

		all_articles.append({
			'filename_title': parts[2],
			'pub_date': pub_date.strftime('%Y-%m-%d'),
			'image': parsed['image'],
			'summary': parsed['summary'],
			'url': f"/cardio-center/articles/{web_url}",
			'filename': web_url
		})

	return JsonResponse({'articles': all_articles})


# ▼▼▼▼▼▼▼▼▼▼ 前端處理 ▼▼▼▼▼▼▼▼▼▼
def cardio_media(request):
	''' 媒體報導主頁 '''
	all_articles = []
	employee_ids = []
	doc_dirs = os.listdir(dir)

	# Step 1：取得 doctor-list 中所有相關科別醫師的 employee_id
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

		filename_title = parts[2]
		date = parts[6]

		try:
			pub_date = datetime.datetime.strptime(date, "%Y-%m-%d")
		except ValueError:
			continue

		web_url = f"{parts[-2]}_{parts[-1].replace('.txt', '')}"  # 文章連結用縮網址
		path = os.path.join(article_dir, post_filename)

		all_articles.append({
			'title': filename_title,
			'pub_date': pub_date,
			'filename': web_url,
			'path': path
		})

	# Step 3：依日期由新到舊排序，只排序一次
	all_articles.sort(key=lambda x: x['pub_date'], reverse=True)

	# Step 4：分頁處理，每頁 20 筆
	paginator = Paginator(all_articles, 20)
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

	return render(request, "cardio_center/cardio_reports.html", {
		'page_obj': page_obj,
		'meta_title': meta_title,
		'meta_summary': meta_summary,
		'meta_image': meta_image,
		'og_image': '',
		'ga_id': '',
		'gtm_id': ''
	})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 醫師陣容 (doctor list) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ▼▼▼▼▼▼▼▼▼▼ 後端處理 ▼▼▼▼▼▼▼▼▼▼
def parse_article_filename(parse_filename):
	"""
	文章獨立頁內容 (標題、發布日期、tag)
	解析檔名：編號_^_標題_^_企劃室_^_日期_^_employee_id
	"""
	parts = parse_filename.replace('.txt', '').split('_')
	return {
		'filename_title': parts[2],
		# 'category': parts[3],
		'pub_date': parts[6],
		'employee_id': parts[7],
		'filename': parse_filename.replace('.txt', '')
	}

def group_stops_by_month(stop_list):
	'''後：將「停休診日期時間」進行按月份分群組，個別傳給模板'''
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
	'''	後：觸發「停休診時間」按鈕，透過 API 取值 '''
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

def parse_doctor_txt(content):
	'''	後：醫師「個人介紹」，txt 標籤內容進行拆解處理，再個別帶入「個人介紹」'''
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

@require_GET
def doctor_sidenav_api(request):
	'''後：醫師「個人介紹-右側選單」，用員工 employee_id，帶入相關醫師列表'''
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

def get_related_articles(employee_id):
	'''後：醫師「相關文章-卡片項目」，用員工 employee_id，帶入與該醫師有關的文章列表'''
	doc_articles = []
	for post_filename in os.listdir(article_dir):
		if post_filename.endswith('.txt') and employee_id in post_filename:
			parts = post_filename.split('_')
			if len(parts) < 8: # 指要要切成幾塊，會影響後面取值順序
				continue
			filename_title = parts[2]
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
				'title': filename_title,
				'pub_date': pub_date,
				'image': parsed['image'],
				'summary': parsed['summary'],
				'blocks': parsed['blocks'],
				# 'filename': filename.replace('.txt', ''),
				'filename': web_url,
			})
	# return doc_articles
	# 根據 pub_date 做由新到舊排序
	doc_articles.sort(key=lambda x: x['pub_date'], reverse=True)
	return doc_articles

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
			'url': f"/cardio-center/articles/{a['filename']}"
		} for a in page_obj]

		return JsonResponse({
			'articles': data,
			'current_page': page_obj.number,
			'num_pages': paginator.num_pages,
		})
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)

def get_related_video(employee_id):
	'''後：醫師「影音專區」，用員工 employee_id，帶入與該醫師有關的影音列表 '''
	video_articles = []

	for video_filename in os.listdir(video_dir):
		if video_filename.endswith('.txt'):
			base_name = video_filename.replace('.txt', '').split('^')[0]
			parts = base_name.split('_')
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


# ▼▼▼▼▼▼▼▼▼▼ 前端處理 ▼▼▼▼▼▼▼▼▼▼
def doctor_list(request):
	'''建立「醫師列表」頁'''
	doctors = []
	doc_dirs = os.listdir(dir)  # ← 每次 request 重新取得

	conn = PLSQLAPI.get_connection()
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

					with open(os.path.join(dir, doc_filename), 'r', encoding='utf-8-sig') as f:
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
						'expertise_list': parsed['expertise_list'],
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
			except Exception:
				pass
	return render(request, 'cardio_center/cardio_doctor_list.html', {
		'doctors': doctors,
		'dept_en': 'CardiovascularMedicine',
		'og_image': '',
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

	with open(os.path.join(dir, matched_file), 'r', encoding='utf-8-sig') as f:
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

	return render(request, 'cardio_center/cardio_doctor_profile.html', {
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
		'dept_en': 'CardiovascularMedicine',
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
	full_filename = None
	for temp_f in os.listdir(article_dir):
		if key_filename in temp_f:
			full_filename = temp_f.replace('.txt', '')
			break # 找到後，就不用再繼續搜尋檔案了

	if not full_filename:
		raise Http404("找不到文章")
	article_path = os.path.join(article_dir, f"{full_filename}.txt")

	if not os.path.exists(article_path):
		raise Http404("找不到文章")

	meta = parse_article_filename(full_filename)
	parsed = parse_article_txt(article_path)

	# 根據 employee_id 取得醫師名稱
	doctor_name = ""
	employee_id = meta.get('employee_id', '')
	if employee_id:
		try:
			# doc_dirs 從前面定義的 dir (醫師資料夾) 取得
			for doc_filename in os.listdir(dir):
				if doc_filename.endswith('.txt') and doc_filename.endswith(f"{employee_id}.txt"):
					name_and_title = doc_filename.rsplit('_', 1)[0].split('_', 2)[-1]
					doctor_name = name_and_title.split(' ')[0]
					break
		except Exception as e:
			pass

	context = {
		# 擷取<h01>、<h>的 title；若 txt 內容沒有設標籤，則取檔名標題
		'article_title': parsed.get('article_title') or meta['filename_title'],
		# 'category': meta['category'],
		'date': meta['pub_date'],
		'employee_id': employee_id,
		'doctor_name': doctor_name,
		'blocks': parsed['blocks'],  # 使用 parse_article_txt() 並傳入 blocks 給模板
		'image': parsed['image'],
		'summary': parsed['summary'],
		'og_image': f"{settings.SITE_DOMAIN}/media/news_2/img/{parsed['og_img']}",
		'dept_en': 'CardiovascularMedicine',
	}
	return render(request, 'cardio_center/cardio_article_detail.html', context)


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 治療項目 (treatment_list) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ▼▼▼▼▼▼▼▼▼▼ 後端處理 ▼▼▼▼▼▼▼▼▼▼
@require_GET
def treatment_sidenav_api(request):
	'''「治療項目文章頁-AJAX 載入側邊選單 / 可切換文章頁面」'''
	treatments = []
	cardio_t_dirs = os.listdir(treat_dir)  # ← 每次 request 重新取得(如果放在全域變數，只會在伺服器啟動時執行一次，之後異動檔案不會更新--因 ajaxao6)
	for treat_filename in cardio_t_dirs:
		if treat_filename.endswith('.txt') and "treat" in treat_filename:
			try:
				parts = treat_filename.rsplit('_', 3)
				filename_title = parts[2]
				url_name = parts[3].replace('.txt', '')
				treatments.append({
					'title': escape(filename_title),
					'url_name': url_name
				})
			except Exception as e:
				continue
	return JsonResponse({'treatments': treatments})

# ▼▼▼▼▼▼▼▼▼▼ 前端處理 ▼▼▼▼▼▼▼▼▼▼
def treatment_list(request):
	'''建立「治療項目」頁'''
	treatments = []
	cardio_t_dirs = os.listdir(treat_dir)  # ← 每次 request 重新取得

	for treat_filename in cardio_t_dirs:
		if treat_filename.endswith('.txt') and ("treat" in treat_filename): # 例.T001_treat_髖關節置換_mako01.txt
			try:
				# 抓出 T001 裡面的數字 → 1
				match = re.search(r'T(\d+)', treat_filename)
				order_num = int(match.group(1)) if match else 9999  # 沒抓到就放後面

				parts = treat_filename.rsplit('_', 3)
				filename_title = parts[2]
				url_name = parts[3].replace('.txt', '')

				# 共用 parse_article_txt 這個函式解析 txt 內容 (函式已有 with open，所以根據參數 filepath 提供檔案路徑)
				treat_path = os.path.join(treat_dir, treat_filename)
				treat_parsed = parse_article_txt(treat_path, detail=False)

				treatments.append({
					'treat_title': filename_title,
					'url_name': url_name,
					'thumb_img': treat_parsed['thumb_img'],
					'summary': treat_parsed.get('summary', ''),
					'order': order_num  # 排序用的欄位
				})
			except Exception as e:
				print(f"錯誤解析 {treat_filename}：{e}")
				continue

	# 根據 'order' 由小到大排序
	treatments.sort(key=lambda x: x['order'])
			
	return render(request, 'cardio_center/cardio_treatment_list.html', {
		'treatments': treatments,
		'og_image': '',
		'ga_id': '', 
		'gtm_id': ''
	})

def treatment_article(request, url_name):
	'''「治療項目文章頁」'''
	cardio_t_dirs = os.listdir(treat_dir)  # ← 每次 request 重新取得
	matched_treat_file = None
	# treat_name = None

	for treat_filename in cardio_t_dirs:
		if treat_filename.endswith('.txt') and treat_filename.endswith(f"{url_name}.txt"):
			matched_treat_file = treat_filename
			treat_name = treat_filename.rsplit('_', 2)[1]
			break

	if not matched_treat_file:
		raise Http404("找不到文章")

	# 引入 parse_article_txt 函式，解析 txt 內容
	treat_path = os.path.join(treat_dir, matched_treat_file)
	treat_parsed = parse_article_txt(treat_path)

	context = {
		'treat_title': treat_name, # 標題取自檔名
		'treat_a_title': treat_parsed['article_title'], # 標題取自 txt 內容
		'blocks': treat_parsed['blocks'],
		'image': treat_parsed['image'],
		'treat_summary': treat_parsed['summary'],
		'og_image': f"{settings.SITE_DOMAIN}/media/cardio_center/cardio_treat_articles/treat_articles_img/{treat_parsed['og_img']}" if treat_parsed.get('og_img') else '',
	}
	return render(request, 'cardio_center/cardio_treat_article_detail.html', context)


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 影音專區 (film) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ▼▼▼▼▼▼▼▼▼▼ 後端處理 ▼▼▼▼▼▼▼▼▼▼
def get_iso_duration(duration_str):
	"""將 05:30 格式的時長轉換成 ISO 8601 的 PT5M30S 格式，利於出現在 Google 搜尋結果的 「影片 (Videos)」分頁"""
	if not duration_str:
		return "PT5M"
	parts = duration_str.split(':')
	try:
		if len(parts) == 2:
			return f"PT{int(parts[0])}M{int(parts[1])}S"
		elif len(parts) == 3:
			return f"PT{int(parts[0])}H{int(parts[1])}M{int(parts[2])}S"
	except ValueError:
		pass
	return "PT5M"

def fetch_youtube_duration_on_the_fly(yt_id):
	"""向 YouTube 網頁抓取影片真實播放長度，並返回分:秒格式"""
	import urllib.request
	import urllib.parse
	import re
	url = f"https://www.youtube.com/watch?v={yt_id}"
	req = urllib.request.Request(
		url, 
		headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
	)
	try:
		with urllib.request.urlopen(req, timeout=5) as response:
			html = response.read().decode('utf-8', errors='ignore')
			m = re.search(r'<meta itemprop="duration" content="([^"]+)">', html)
			if m:
				m_dur = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', m.group(1))
				if m_dur:
					hours = int(m_dur.group(1)) if m_dur.group(1) else 0
					minutes = int(m_dur.group(2)) if m_dur.group(2) else 0
					seconds = int(m_dur.group(3)) if m_dur.group(3) else 0
					if hours > 0:
						return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
					else:
						return f"{minutes:02d}:{seconds:02d}"
			
			m_ms = re.search(r'"approxDurationMs":"(\d+)"', html)
			if m_ms:
				total_seconds = int(m_ms.group(1)) // 1000
				minutes = total_seconds // 60
				seconds = total_seconds % 60
				return f"{minutes:02d}:{seconds:02d}"
	except Exception as e:
		print(f"Error fetching YouTube duration for {yt_id}: {e}")
	return None

@require_GET
def cardio_film_api(request):
	"""Ajax 回傳影音專區影片（同時掃描 video_dir 與 Films_Dir，video_dir 仍以 doctor-list 過濾）、支援分頁"""
	try:
		employee_ids = get_active_doctor_ids()  # 取 doctor-list 中的乳房外科醫師 employee_id
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

				# 優先拿掉 ^hash 後綴以還原乾淨檔名，並取得 video_key
				name = video_filename.replace('.txt', '')
				video_key = ""
				if '^' in name:
					name_clean, video_key = name.split('^', 1)
				else:
					name_clean = name

				video_data = {
					'title': '',
					'date': '',
					'doctor_id': '',
					'youtube_url': '',
					'youtube_image': '',
					'youtube_id': '',
					'duration': '',
					'category_index': None,
					'description': '',
					'video_key': video_key,
					'duration_iso': '',
					'filename_title': ''
				}

				for line in lines:
					if line.startswith('<yh>'):
						full_title = line.replace('<yh>', '').strip()
						title_parts = re.split(r'[／/]', full_title)
						video_data['title'] = title_parts[0].strip()
						if len(title_parts) > 1:
							video_data['description'] = title_parts[1].strip()
					elif line.startswith('<yd>'):
						video_data['date'] = line.replace('<yd>', '').strip()
					elif line.startswith('<dr>'):
						video_data['doctor_id'] = line.replace('<dr>', '').strip()
					elif line.startswith('<vd>'):
						video_data['duration'] = line.replace('<vd>', '').strip()
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
							video_data['youtube_id'] = ytb_id
							video_data['youtube_image'] = f'https://img.youtube.com/vi/{ytb_id}/maxresdefault.jpg'

				video_data['filename_title'] = name_clean.split('_')[1].strip() if '_' in name_clean else name_clean
				# 若檔案內沒提供標題，嘗試從檔名取得
				if not video_data['title']:
					video_data['title'] = video_data['filename_title']

				# 若沒有 youtube_image，但有 youtube_url，嘗試再以 regex 解析一次
				if not video_data['youtube_image'] and video_data['youtube_url']:
					u = video_data['youtube_url']
					m = re.search(r'(?:v=|embed/|youtu\.be/)([^&\s?/]+)', u)
					if m:
						ytb_id = m.group(1)
						video_data['youtube_id'] = ytb_id
						video_data['youtube_image'] = f'https://img.youtube.com/vi/{ytb_id}/maxresdefault.jpg'

				# 若讀取後缺乏時長資料，則自動動態向 YouTube 抓取並回寫檔案
				if not video_data['duration'] and video_data['youtube_url']:
					u = video_data['youtube_url']
					m = re.search(r'(?:v=|embed/|youtu\.be/)([^&\s?/]+)', u)
					if m:
						ytb_id = m.group(1)
						duration = fetch_youtube_duration_on_the_fly(ytb_id)
						if duration:
							video_data['duration'] = duration
							try:
								with open(filepath, 'r', encoding='utf-8-sig') as f_read:
									orig_content = f_read.read()
								ending = "" if orig_content.endswith('\n') else "\n"
								with open(filepath, 'a', encoding='utf-8') as f_write:
									f_write.write(f"{ending}<vd>{duration}\n")
							except Exception as write_err:
								print(f"Error auto-writing duration to {filepath}: {write_err}")

				# 解析分類索引值
				category_index = None
				parts = name_clean.split('_')
				if len(parts) >= 2:
					if parts[-1].isdigit():
						category_index = int(parts[-1])
					elif len(parts) >= 3 and parts[-2].isdigit():
						category_index = int(parts[-2])
				video_data['category_index'] = category_index

				# 計算 ISO 時長
				video_data['duration_iso'] = get_iso_duration(video_data['duration'])

				all_videos.append(video_data)

		# **如果沒有影片，直接回傳提示**
		if not all_videos:
			return JsonResponse({
				'videos': [],
				'current_page': 1,
				'total_pages': 0,
				'message': '目前暫無影音文章'
			})
		
		# 以 date 欄位排序（字串），空日期會排到後面
		all_videos.sort(key=lambda x: x.get('date', ''), reverse=True)

		# 支援不分頁載入所有影片
		per_page_param = request.GET.get("per_page")
		if per_page_param == 'all':
			return JsonResponse({
				'videos': all_videos,
				'current_page': 1,
				'total_pages': 1
			})

		# 分頁，每頁 20 筆
		per_page = int(per_page_param) if per_page_param and per_page_param.isdigit() else 20
		paginator = Paginator(all_videos, per_page)
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

# ▼▼▼▼▼▼▼▼▼▼ 前端處理 ▼▼▼▼▼▼▼▼▼▼
def cardio_film(request):
	"""影音專區主頁，初始渲染不載入影片內容，由 AJAX 呼叫 health_film_api 動態載入；附帶回傳是否存在 Films_Dir 的簡單狀態供前端使用"""
	append_crc32_to_filenames()  # 自動將尚未有 hash 的影片 txt 命名為 ...^hash.txt
	has_films_dir = os.path.exists(Films_Dir) and any(f.endswith('.txt') for f in os.listdir(Films_Dir))
	return render(request, "cardio_center/cardio_film.html", {
		'og_image': '',
		'ga_id': '',
		'gtm_id': '',
		'has_films_dir': has_films_dir
	})

def cardio_film_detail(request, video_key):
	"""影音專區-爬蟲與直接瀏覽專用獨立詳細頁 (O(1) 效能定位)"""
	search_dirs = [video_dir, Films_Dir]
	found_filepath = None

	# 使用 os.listdir 比對檔名，避免開啟所有檔案，維持高載入效能
	for d in search_dirs:
		if not os.path.exists(d):
			continue
		for fname in os.listdir(d):
			if fname.endswith(f"^{video_key}.txt"):
				found_filepath = os.path.join(d, fname)
				break
		if found_filepath:
			break

	if not found_filepath:
		raise Http404("找不到該影音文章")

	with open(found_filepath, 'r', encoding='utf-8-sig') as f:
		lines = f.read().splitlines()

	video = {
		'yt_title': '',
		'date': '',
		'doctor_id': '',
		'duration': '',
		'youtube_url': '',
		'youtube_id': '',
		'youtube_image': '',
		'description': '',
		'video_key': video_key,
		'duration_iso': '',
		'filename_title': ''
	}

	for line in lines:
		if line.startswith('<yh>'):
			full_title = line.replace('<yh>', '').strip()
			title_parts = re.split(r'[／/]', full_title)
			video['yt_title'] = title_parts[0].strip()
			if len(title_parts) > 1:
				video['description'] = title_parts[1].strip()
		elif line.startswith('<yd>'):
			video['date'] = line.replace('<yd>', '').strip()
		elif line.startswith('<dr>'):
			video['doctor_id'] = line.replace('<dr>', '').strip()
		elif line.startswith('<vd>'):
			video['duration'] = line.replace('<vd>', '').strip()
		elif line.startswith('<ytb>'):
			ytb_url = line.replace('<ytb>', '').strip()
			video['youtube_url'] = ytb_url

			m = re.search(r'(?:v=|embed/|youtu\.be/)([^&\s?/]+)', ytb_url)
			if m:
				ytb_id = m.group(1)
				video['youtube_id'] = ytb_id
				video['youtube_image'] = f'https://img.youtube.com/vi/{ytb_id}/maxresdefault.jpg'

	name = os.path.basename(found_filepath).replace('.txt', '').split('^')[0]
	video['filename_title'] = name.split('_')[1].strip() if '_' in name else name

	video['duration_iso'] = get_iso_duration(video['duration'])

	return render(request, "cardio_center/cardio_film_detail.html", {'video': video})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 衛教園地 (edu) ■■■■■■■■■■■■■■■■■■■■■■■■■■

# ▼▼▼▼▼▼▼▼▼▼ 後端處理 ▼▼▼▼▼▼▼▼▼▼
def get_health_edu_items():
	"""取得衛教園地分組後的資料（list of (filename_title, title_hash, images, [optional] is_txt, [optional] thumb)）"""
	# 優化：先從快取中尋找資料
	cache_key = 'cardio_edu_items_metadata_v4' # 檔名邏輯更新，更新快取 key
	cached_data = cache.get(cache_key)
	if cached_data:
		return cached_data, os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc', '0_內科_InternalMedicine', '心臟血管內科_CardiovascularMedicine')

	# 1. 處理舊有的純圖片衛教資料
	base_path = os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc', '0_內科_InternalMedicine', '心臟血管內科_CardiovascularMedicine')
	image_files = [f for f in os.listdir(base_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

	grouped_images = defaultdict(list)
	for filename in image_files:
		parts = filename.split('_page')
		if len(parts) >= 2:
			title = parts[0]
			grouped_images[title].append(filename)

	formatted_items = []
	for filename_title, images in grouped_images.items():
		images.sort(key=lambda name: int(name.split('page-')[-1].split('.')[0]))
		title_hash = hashlib.md5(filename_title.encode('utf-8')).hexdigest()[:8]
		formatted_items.append((filename_title, title_hash, images, False, None))

	# 2. 處理新的 E001 .txt 衛教文章
	edu_txt_dir = os.path.join(settings.MEDIA_ROOT, 'cardio_center', 'cardio_edu')
	edu_icon_dir = os.path.join(edu_txt_dir, 'edu-icon')
	
	# 先讀取所有目前的 icon 檔名，用於快速比對
	icon_files = os.listdir(edu_icon_dir) if os.path.exists(edu_icon_dir) else []

	if os.path.exists(edu_txt_dir):
		txt_files = [f for f in os.listdir(edu_txt_dir) if f.startswith('E001') and f.endswith('.txt')]
		for filename in txt_files:
			# 解析檔名標題：E001_edu_標題_日期.txt
			parts = filename.replace('.txt', '').split('_')
			if len(parts) >= 3:
				filename_title = parts[2]
				prefix = "_".join(parts[:3]) # E001_edu_標題
			else:
				filename_title = filename.replace('.txt', '')
				prefix = filename_title
			
			# 優先從檔名擷取 ^hash，若無則跳過 (需先經過 append_crc32_to_filenames 處理)
			title_hash = ""
			if '^' in filename:
				title_hash = filename.replace('.txt', '').split('^')[-1]
			else:
				# 備註：如果不想要自動跳過未改名的檔案，可以保留舊的 md5 邏輯作為 fallback
				# title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:8]
				continue
			
			# 從檔名對應縮圖，不讀取檔案內容
			thumb_filename = ""
			for icon_f in icon_files:
				if icon_f.startswith(prefix) and icon_f.lower().endswith(('.jpg', '.jpeg', '.png')):
					thumb_filename = icon_f
					break
			
			# 轉換縮圖為 WebP
			thumb_rel_path = ""
			if thumb_filename:
				thumb_rel_path = convert_edu_icon_image_to_webp(thumb_filename)
			
			formatted_items.append((filename_title, title_hash, filename, True, thumb_rel_path))

	# 根據標題文字排序
	formatted_items.sort(key=lambda x: x[0])
	
	# 維護新增 .txt 後，前台約 5 分鐘顯示
	cache.set(cache_key, formatted_items, timeout=300)
	
	return formatted_items, base_path

@require_GET
def cardio_edu_api(request):
	'''支援 ajax 分頁'''
	page = int(request.GET.get("page", 1))
	per_page = int(request.GET.get("per_page", 20))
	all_items, base_path = get_health_edu_items()
	paginator = Paginator(all_items, per_page)
	page_obj = paginator.get_page(page)
	
	image_media_url = settings.MEDIA_URL + 'health_edu/Doc/0_內科_InternalMedicine/心臟血管內科_CardiovascularMedicine/'
	
	data = []
	for item in page_obj:
		filename_title, title_hash, content, is_txt, thumb = item
		if is_txt:
			# 此處 thumb 已經是 media 相對路徑，例如 "xxx_center/xxx_edu/edu_icon/thumb_webp/xxx.webp"
			data.append({
				'title': filename_title,
				'titleId': title_hash,
				'images': [settings.MEDIA_URL + thumb] if thumb else [],
				'is_txt': True
			})
		else:
			# 此處 content 為圖片清單
			data.append({
				'title': filename_title,
				'titleId': title_hash,
				'images': [image_media_url + img for img in content],
				'is_txt': False
			})

	return JsonResponse({
		'items': data,
		'current_page': page_obj.number,
		'num_pages': paginator.num_pages,
	})

@require_GET
def random_cardio_edus_api(request):
	"""隨機取得 5 筆衛教園地項目（供 xxx_article_detail 側欄卡片用）"""
	all_items, base_path = get_health_edu_items()
	media_url = settings.MEDIA_URL + 'health_edu/Doc/0_內科_InternalMedicine/心臟血管內科_CardiovascularMedicine/'

	# 隨機挑選最多 5 筆
	random_items = random.sample(all_items, min(5, len(all_items)))

	edu_data = []
	for item in random_items:
		filename_title, title_hash, content, is_txt, thumb = item
		
		# 決定縮圖路徑
		if is_txt:
			# .txt 檔案使用 WebP 縮圖路徑
			thumb_image_url = settings.MEDIA_URL + thumb if thumb else ''
		else:
			# 圖片組使用第一張圖的路徑
			thumb_image = content[0] if content else ''
			thumb_image_url = media_url + thumb_image if thumb_image else ''

		edu_data.append({
			'filename_title': filename_title,
			'thumb_image': thumb_image_url,
			'title_id': title_hash
		})

	return JsonResponse({'edus': edu_data})

# ▼▼▼▼▼▼▼▼▼▼ 前端處理 ▼▼▼▼▼▼▼▼▼▼
def cardio_edu(request):
	'''衛教園地-各科別主列表'''
	append_crc32_to_filenames() # 自動重命名衛教文章檔案 (加上 ^hash)
	all_items, base_path = get_health_edu_items()
	paginator = Paginator(all_items, 20)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	context = {
		'media_url': settings.MEDIA_URL + 'health_edu/Doc/0_內科_InternalMedicine/心臟血管內科_CardiovascularMedicine/',
		'page_obj': page_obj,
		'og_image': '',
	}
	return render(request, 'cardio_center/cardio_edu.html', context)

@require_GET
def cardio_edu_detail(request, title_id):
	"""衛教園地詳細頁面"""
	all_items, base_path = get_health_edu_items()
	
	matched_item = None
	# 2026-02-08 更新：支援透過檔名中的 Hash 值尋找檔案
	for title, title_hash, content, is_txt, thumb in all_items:
		if title_id == title_hash:
			matched_item = (title, content, is_txt)
			break
		# 這裡保留一個保險：如果網址帶的是舊的標題(中文)，也嘗試匹配 (雖然以後會失效)
		if title_id == title:
			matched_item = (title, content, is_txt)
			break

	if not matched_item:
		raise Http404("找不到該筆衛教資料")

	filename_title, content, is_txt = matched_item
	
	if is_txt:
		# 文字檔模式
		edu_txt_dir = os.path.join(settings.MEDIA_ROOT, 'cardio_center', 'cardio_edu')
		filepath = os.path.join(edu_txt_dir, content)
		parsed = parse_article_txt(filepath)
		
		# 找出第一個圖片作為 og_image
		og_image_path = ""
		for block in parsed['blocks']:
			if block['type'] == 'img' and block.get('edu_article_src'):
				og_image_path = f"/media/{block['edu_article_src']}"
				break

		return render(request, 'cardio_center/cardio_edu_detail.html', {
			'title': filename_title,
			'blocks': parsed['blocks'],
			'is_txt': True,
			'images': [], # 確保 JS 變數不會噴錯
			'og_image': f"{settings.SITE_DOMAIN}{og_image_path}" if og_image_path else '',
		})
	else:
		# 純圖片模式，比照 health_edu 邏輯加入 webp 轉換
		_dir = base_path
		_webp_dir = os.path.join(_dir, 'webp')
		os.makedirs(_webp_dir, exist_ok=True)

		image_list = []
		MEDIA_URL = settings.MEDIA_URL
		base_url_path = "health_edu/Doc/0_內科_InternalMedicine/心臟血管內科_CardiovascularMedicine"

		for file in content:
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

			jpg_url = f"{MEDIA_URL}{base_url_path}/{file}"
			if has_webp:
				webp_url = f"{MEDIA_URL}{base_url_path}/webp/{webp_name}"
			else:
				webp_url = jpg_url

			image_list.append({
				'jpg_url': jpg_url,
				'webp_url': webp_url,
				'has_webp': has_webp
			})

		return render(request, 'cardio_center/cardio_edu_detail.html', {
			'title': filename_title,
			'image_list': image_list,
			'is_txt': False,
			'og_image': f"{settings.SITE_DOMAIN}{image_list[0]['jpg_url']}" if image_list else '',
		})


# ■■■■■■■■■■■■■■■■■■■■■■■■■■ 聯絡我們 (contact) ■■■■■■■■■■■■■■■■■■■■■■■■■■
@ratelimit_form_submit(max_requests=5, window=300, redirect_url='cardio_send_mail')  # 5 分鐘內最多 5 次提交
@captcha_failure_limit(max_failures=5, lockout_time=300, redirect_url='cardio_send_mail', captcha_field='captcha')  # 5 次驗證碼錯誤後鎖定 5 分鐘
def cardio_send_mail(request):
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
				return render(request, "cardio_center/cardio_contact.html", {
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
					return redirect('cardio_send_mail')
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
			return render(request, "cardio_center/cardio_contact.html", {
				"form": form,
				'og_image': '',
				'ga_id': '',
				'gtm_id': ''
			})
	else:
		# GET 請求：顯示空表單
		form = ContactForm()

	return render(request, "cardio_center/cardio_contact.html", {
		"form": form,
		'og_image': '',
		'ga_id': '',
		'gtm_id': ''
	})