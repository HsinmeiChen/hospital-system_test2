from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect

import re
import os
import datetime
import random

from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger #分頁功能套件，Django本身就有支援
from django.conf import settings

class MyPaginator(Paginator):
	"""docstring for MyPaginator"""
	def __init__(self, object_list, per_page, show_count = 1, orphans = 0, allow_empty_first_page = True):
		super().__init__(object_list, per_page, orphans, allow_empty_first_page)
		self.show_count = show_count
		self.has_previous_more = True
		self.has_next_more = True

	def page(self, number):
		self.number = int(number)

		if(self.number <= self.show_count + 2):
			self.has_previous_more = False
			self.previous_range = range(1, self.number)
		else:
			self.previous_range = range(self.number - self.show_count, self.number)

		if(self.number >= self.num_pages - self.show_count - 1):
			self.has_next_more = False
			self.next_range = range(self.number + 1, self.num_pages + 1)
		else:
			self.next_range = range(self.number + 1, self.number + self.show_count + 1)
		return super().page(number)

def _find_category_by_en(sub_item_en):
	"""
	根據英文子科室名稱（如 'Pharmacy'）動態搜尋並回傳其主資料夾與子資料夾路徑資訊。
	"""
	_base_dir = os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc')
	if not os.path.exists(_base_dir):
		return None
	for main_dir in os.listdir(_base_dir):
		if not os.path.isdir(os.path.join(_base_dir, main_dir)):
			continue
		for sub_dir in os.listdir(os.path.join(_base_dir, main_dir)):
			if "_" in sub_dir:
				parts = sub_dir.split("_")
				if len(parts) > 1 and parts[1].lower() == sub_item_en.lower():
					return {
						"main_folder": main_dir,
						"sub_folder": sub_dir,
						"main_chinese": main_dir.split("_")[1] if len(main_dir.split("_")) > 1 else main_dir,
						"sub_chinese": parts[0]
					}
	return None

def menu_f():
	collapse_List=[]
	_dir=os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc')
	_url_dir=r'\public\Doc'
	data=os.listdir(_dir)
	i=0
	for d in data:
		if not os.path.isdir(os.path.join(_dir, d)):
			continue
		parts = d.split("_")
		index_prefix = parts[0]
		chinese_name = parts[1] if len(parts) > 1 else d
		english_name = parts[2] if len(parts) > 2 else ""

		collapse_List.append({
			"index": i+1,
			"file": d,                    # 原始資料夾名稱 (如 '4_其它_Other')
			"showfile": chinese_name,     # 中文顯示名稱 (如 '其它')
			"en_name": english_name,      # 英文顯示名稱 (如 'Other')
			"url_dir": _url_dir+'\\'+d,
			"dir": os.path.join(_dir,d)
		})
		i+=1

	i=0
	for c in collapse_List:
		pic_list = os.listdir(c['dir'])
		pic_list2=[]
		ii=1
		for aa in pic_list:
			if os.path.isdir(os.path.join(c['dir'], aa)):
				parts = aa.split("_")
				chinese_sub = parts[0]
				english_sub = parts[1] if len(parts) > 1 else aa
				pic_list2.append({
					"index": ii,
					"name": aa,              # 原始子資料夾名稱 (如 '藥局_Pharmacy')
					"show_name": chinese_sub, # 中文顯示名稱 (如 '藥局')
					"en_name": english_sub    # 英文 URL 名稱 (如 'Pharmacy')
				})
				ii+=1
		collapse_List[i]["sub_item"] = pic_list2
		i+=1
	return collapse_List

def get_image_name_index(item):
	return item[0]
def get_image_name(item):
	return item[1]
def get_image_page(item):
	return item[2]
def get_time_str(item):
	return item[4]
def remove_duplicate_items(_api_data, _key):
	unique_elements = []
	cleaned_data = []
	keys = []
	for i, j in enumerate(_api_data):
		if _api_data[i][_key] not in unique_elements:
			unique_elements.append(_api_data[i][_key])
			keys.append(i)

	for key in keys:
		cleaned_data.append(_api_data[key])

	return cleaned_data


@csrf_exempt
def index(request):
	collapse_List=menu_f()

	data_files = []
	data_paths = []
	pic_lists=[]
	info_data=[]
	message_lists=[]
	_dir=os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc')

	data = os.listdir(_dir)
	for d in data:
		if not os.path.isdir(os.path.join(_dir, d)):
			continue
		d_dir = os.listdir(os.path.join(_dir, d))
		for dd in d_dir:
			if not os.path.isdir(os.path.join(_dir, d, dd)):
				continue
			dd_dir = os.listdir(os.path.join(_dir, d, dd))
			for ddd in dd_dir:
				data_files.append([ddd, os.path.join(_dir, d, dd)])

	data_files.sort(key=lambda x: x[0])

	i=0
	for file in data_files:
		if(".jpg" in file[0]):
			file_path=os.path.join(file[1],file[0])
			unix_time = os.path.getmtime(file_path)
			datetimeObj = datetime.datetime.fromtimestamp(unix_time)
			dateStr = datetimeObj.strftime('%Y-%m-%d')

			pic_lists.append(file[0].split("_"))
			pic_lists[i].insert(0,"D00"+str(i))
			pic_lists[i].append(file[0])
			pic_lists[i].append(dateStr)
			pic_lists[i].append(file[1])
			i+=1
	
	for p in pic_lists:
		temp_arr=[];
		for f in pic_lists:
			if get_image_name(p) in f[1]:
				temp_arr.append(f[3])
		temp_arr.sort()
		main_item = os.path.basename(os.path.dirname(p[5]))
		sub_item = os.path.basename(p[5])
		sub_item_en = sub_item.split("_")[1] if "_" in sub_item else sub_item
		import hashlib
		name_hash = hashlib.md5(get_image_name(p).encode('utf-8')).hexdigest()[:8]
		message_lists.append(
			{"index":p[0],
			"name":get_image_name(p),
			"hash":name_hash,
			"arr":temp_arr ,
			"main_item":main_item ,
			"sub_item":sub_item ,
			"sub_item_en":sub_item_en ,
			"time":get_time_str(p)})
	message_lists=remove_duplicate_items(message_lists,"name")
	message_lists.sort(key=lambda x: (x["time"], x["name"]), reverse=True)

	page_limit=8
	paginator_2 = MyPaginator(message_lists, page_limit)
	total_2 = int(paginator_2.num_pages)
	page_2 = request.GET.get('page', 1)
	contacts_2 = paginator_2.page(page_2)

	message_lists_cut=contacts_2

	MEDIA_URL = settings.MEDIA_URL
	return render(request, "Health_Edu_index.html", {
		'collapse_List': collapse_List,
		'message_lists_cut': message_lists_cut,
		'contacts_2': contacts_2,
		'paginator_2': paginator_2,
		'MEDIA_URL': MEDIA_URL,
	})

@csrf_exempt
def index2(request, sub_item_en):
	collapse_List=menu_f()

	category_info = _find_category_by_en(sub_item_en)
	if not category_info:
		return redirect('index')

	main_item = category_info["main_folder"]
	sub_item = category_info["sub_folder"]
	showfile = category_info["main_chinese"]
	sub_item_chinese = category_info["sub_chinese"]

	pic_lists=[]
	info_data=[]
	message_lists=[]
	_dir=os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc', main_item, sub_item)
	data = os.listdir(_dir)

	i=0
	for file in data:
		if(".jpg" in file):
			file_path=os.path.join(_dir,file)
			unix_time = os.path.getmtime(file_path)
			datetimeObj = datetime.datetime.fromtimestamp(unix_time)
			dateStr = datetimeObj.strftime('%Y-%m-%d')

			pic_lists.append(file.split("_"))
			pic_lists[i].insert(0,"D00"+str(i))
			pic_lists[i].append(file)
			pic_lists[i].append(dateStr)
			i+=1
	pic_lists.sort(key=get_image_name)

	for p in pic_lists:
		temp_arr=[];
		for f in pic_lists:
			if get_image_name(p) in f[1]:
				temp_arr.append(f[3])
		import hashlib
		name_hash = hashlib.md5(get_image_name(p).encode('utf-8')).hexdigest()[:8]
		message_lists.append({"index":p[0],"name":get_image_name(p),"hash":name_hash,"arr":temp_arr ,"time":get_time_str(p)})
	message_lists=remove_duplicate_items(message_lists,"name")
	message_lists.sort(key=lambda x: (x["time"], x["name"]), reverse=True)

	page_limit=8
	paginator_2 = MyPaginator(message_lists, page_limit)
	total_2 = int(paginator_2.num_pages)
	page_2 = request.GET.get('page', 1)
	contacts_2 = paginator_2.page(page_2)

	message_lists_cut=contacts_2
	MEDIA_URL = settings.MEDIA_URL
	return render(request, "Health_Edu_index2.html", {
		'collapse_List': collapse_List,
		'showfile': showfile,
		'sub_item_chinese': sub_item_chinese,
		'sub_item_en': sub_item_en,
		'main_item': main_item,
		'sub_item': sub_item,
		'message_lists_cut': message_lists_cut,
		'contacts_2': contacts_2,
		'paginator_2': paginator_2,
		'MEDIA_URL': MEDIA_URL,
	})


@csrf_exempt
def search_page(request):
	search_text = request.GET.get('search_text', '').strip()
	collapse_List = menu_f()
	_base_dir = os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc')
	message_lists = []

	if search_text and os.path.exists(_base_dir):
		baseDir_list = os.listdir(_base_dir)
		idx = 0
		for base_folder in baseDir_list:
			if not os.path.isdir(os.path.join(_base_dir, base_folder)):
				continue
			r_department = base_folder.split("_")[1] if "_" in base_folder else base_folder
			_main_dir = os.path.join(_base_dir, base_folder)
			subDir_list = os.listdir(_main_dir)
			for sub_folder in subDir_list:
				_sub_dir = os.path.join(_main_dir, sub_folder)
				if not os.path.isdir(_sub_dir):
					continue
				pic_list = os.listdir(_sub_dir)
				unique_titles = set()
				for file in pic_list:
					if file.lower().endswith('.jpg') and '_' in file:
						title = file.split('_')[0]
						if search_text in title:
							unique_titles.add(title)
				for title in unique_titles:
					idx += 1
					sub_item_en = sub_folder.split("_")[1] if "_" in sub_folder else sub_folder
					import hashlib
					name_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:8]
					message_lists.append({
						"index": idx,
						"r_department": r_department,
						"room": sub_folder.split("_")[0] if "_" in sub_folder else sub_folder,
						"sub_item_en": sub_item_en,
						"name": title,
						"hash": name_hash,
						"department": base_folder
					})

	# 設定分頁功能
	page_limit = 10
	paginator_2 = MyPaginator(message_lists, page_limit)
	page_2 = request.GET.get('page', 1)
	contacts_2 = paginator_2.page(page_2)
	message_lists_cut = contacts_2

	MEDIA_URL = settings.MEDIA_URL
	return render(request, "Health_Edu_search.html", {
		'collapse_List': collapse_List,
		'message_lists_cut': message_lists_cut,
		'contacts_2': contacts_2,
		'paginator_2': paginator_2,
		'search_text': search_text,
		'MEDIA_URL': MEDIA_URL,
	})

@csrf_exempt
def detail_page(request, sub_item_en, title_name):
	collapse_List = menu_f()

	category_info = _find_category_by_en(sub_item_en)
	if not category_info:
		return redirect('index')

	main_item = category_info["main_folder"]
	sub_item = category_info["sub_folder"]

	_dir = os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc', main_item, sub_item)
	if not os.path.exists(_dir):
		return redirect('index')

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

	# 若皆找不到，導回首頁
	if not real_title:
		return redirect('index')

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
		jpg_url = f"{MEDIA_URL}health_edu/Doc/{main_item}/{sub_item}/{file}"
		if has_webp:
			webp_url = f"{MEDIA_URL}health_edu/Doc/{main_item}/{sub_item}/webp/{webp_name}"
		else:
			webp_url = jpg_url

		image_list.append({
			'jpg_url': jpg_url,
			'webp_url': webp_url,
			'has_webp': has_webp
		})

	return render(request, "Health_Edu_detail.html", {
		'collapse_List': collapse_List,
		'main_item': main_item,
		'sub_item': sub_item,
		'sub_item_en': sub_item_en,
		'sub_item_chinese': category_info["sub_chinese"],
		'title_name': real_title,
		'image_list': image_list,
		'MEDIA_URL': MEDIA_URL,
	})
