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

def menu_f():

	collapse_List=[]
	_dir=os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc')#C:\Python_Test\virtualenv\KP
	_url_dir=r'\public\Doc'
	data=os.listdir(_dir)
	i=0
	for d in data:
		# "if_click":("Y" if d==main_item else "N"),
		sub_name = d.split("_")[1]
		collapse_List.append(
			{"index":i+1,
			 "file":d,
			 "showfile":sub_name,
			 "url_dir":_url_dir+'\\'+d,
			 "dir":os.path.join(_dir,d)})
		i+=1

	i=0
	for c in collapse_List:
		pic_list = os.listdir(c['dir'])
		pic_list2=[]
		ii=1
		for aa in pic_list:
			pic_list2.append({"index":ii,"name":aa})
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
		d_dir = os.listdir(os.path.join(_dir, d))
		for dd in d_dir:
			dd_dir = os.listdir(os.path.join(_dir, d, dd))
			for ddd in dd_dir:
				data_files.append([ddd, os.path.join(_dir, d, dd)])
				# data_paths.append(_dir + "\\" + d + "\\" + dd)

	# datas = zip(data_files, data_paths)
	random.shuffle(data_files)

	i=0
	for file in data_files:
		if(".jpg" in file[0]):
			file_path=os.path.join(file[1],file[0])
			#取得檔案修改時間os.path.getmtime，如果要用創立時間 用 os.path.getctime
			unix_time = os.path.getctime(file_path)
			#轉時間物件
			datetimeObj = datetime.datetime.fromtimestamp(unix_time)
			#轉字串
			dateStr = datetimeObj.strftime('%Y-%m-%d')

			pic_lists.append(file[0].split("_"))
			pic_lists[i].insert(0,"D00"+str(i))
			pic_lists[i].append(file[0])
			pic_lists[i].append(dateStr)
			pic_lists[i].append(file[1])
			i+=1
	# pic_lists.sort(key=get_image_name)
	
	for p in pic_lists:
		temp_arr=[];
		for f in pic_lists:
			if get_image_name(p) in f[1]:
				temp_arr.append(f[3])
		temp_arr.sort()
		# print("p",p)
		# print("p[5]",p[5])
		main_item = os.path.basename(os.path.dirname(p[5]))
		sub_item = os.path.basename(p[5])
		message_lists.append(
			{"index":p[0],
			"name":get_image_name(p),
			"arr":temp_arr ,
			"main_item":main_item ,
			"sub_item":sub_item ,
			"time":get_time_str(p)})
	message_lists=remove_duplicate_items(message_lists,"name")
	message_lists.sort(key=lambda x: x["time"])

	# 步驟(六)、設定分頁功能
	page_limit=8
	paginator_2 = MyPaginator(message_lists, page_limit) # 設定一頁要顯示幾筆
	total_2 = int(paginator_2.num_pages) # 將筆數計算總共有幾頁
	page_2 = request.GET.get('page', 1) # 接收使用者點選的頁碼
	contacts_2 = paginator_2.page(page_2) # (列表清單用變數) 回傳使用者點的頁碼，讓前台顯示 (取得第幾頁的內容再丟回contacts)

	message_lists_cut=contacts_2

	MEDIA_URL = settings.MEDIA_URL
	return render(request, "Health_Edu_index.html",locals())
@csrf_exempt
def index2(request,main_item,sub_item):
	collapse_List=menu_f()

	showfile = main_item.split("_")[1]

	pic_lists=[]
	info_data=[]
	message_lists=[]
	_dir=os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc', main_item, sub_item)
	data = os.listdir(_dir)

	# if not(main_item=="" or sub_item==0):
	i=0
	for file in data:
		if(".jpg" in file):
			file_path=os.path.join(_dir,file)
			#取得檔案修改時間os.path.getmtime，如果要用創立時間 用 os.path.getctime
			unix_time = os.path.getctime(file_path)
			#轉時間物件
			datetimeObj = datetime.datetime.fromtimestamp(unix_time)
			#轉字串
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
		message_lists.append({"index":p[0],"name":get_image_name(p),"arr":temp_arr ,"time":get_time_str(p)})
	message_lists=remove_duplicate_items(message_lists,"name")
	message_lists.sort(key=lambda x: x["time"])

	# 步驟(六)、設定分頁功能
	page_limit=8
	paginator_2 = MyPaginator(message_lists, page_limit) # 設定一頁要顯示幾筆
	total_2 = int(paginator_2.num_pages) # 將筆數計算總共有幾頁
	page_2 = request.GET.get('page', 1) # 接收使用者點選的頁碼
	contacts_2 = paginator_2.page(page_2) # (列表清單用變數) 回傳使用者點的頁碼，讓前台顯示 (取得第幾頁的內容再丟回contacts)

	message_lists_cut=contacts_2
	# message_lists=set(message_lists)
	MEDIA_URL = settings.MEDIA_URL
	return render(request, "Health_Edu_index2.html",locals())

# #兒科
# @csrf_exempt
# def health_1(request):
# 	pic_lists=[]
# 	info_data=[]
# 	message_lists=[]

# 	data= os.listdir(r"C:\Python_Test\KP\public\Doc\婦兒科\兒科")

# 	i=0
# 	for file in data:
# 		if(".jpg" in file):
# 			pic_lists.append(file.split("_"))
# 			pic_lists[i].insert(0,"D00"+str(i))
# 			pic_lists[i].append(file)
# 			i+=1
# 	pic_lists.sort(key=get_image_name)
# 	print(pic_lists)

# 	# for pic in pic_list:
# 	return render(request, "Health_Edu_1.html",locals())


# @csrf_exempt
# def Health_Edu_menu(request):

# 	# collapse_List=[]
# 	# _dir=r'C:\Python_Test\KP\media\health_edu\Doc'#C:\Python_Test\virtualenv\KP
# 	# _url_dir=r'\public\Doc'
# 	# data=os.listdir(_dir)
# 	# i=0
# 	# for d in data:
# 	# 	collapse_List.append({"index":i+1,"file":d,"url_dir":_url_dir+'\\'+d,"dir":os.path.join(_dir,d)})
# 	# 	i+=1

# 	# i=0
# 	# for c in collapse_List:
# 	# 	pic_list = os.listdir(c['dir'])
# 	# 	pic_list2=[]
# 	# 	ii=1
# 	# 	for aa in pic_list:
# 	# 		pic_list2.append({"index":ii,"name":aa})
# 	# 		ii+=1
# 	# 	collapse_List[i]["sub_item"] = pic_list2
# 	# 	i+=1
# 	collapse_List=menu_f()
# 	# print(collapse_List)
# 	return render(request, "Health_Edu_menu.html",locals())


@csrf_exempt
def search_page(request):
	# print(request)
	search_text=request.GET.get('search_text')

	# print(tt)
	# META=request.META
	# # print(META)
	# QUERY_STRING=META['QUERY_STRING']
	# # print(QUERY_STRING)
	# search_text=META['search_text']
	collapse_List=menu_f()
	_base_dir=os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc')
	baseDir_list=os.listdir(_base_dir)
	message_lists=[];
	if search_text!="":
		i=0
		for base_folder in baseDir_list:
			_main_dir=os.path.join(_base_dir,base_folder)
			subDir_list=os.listdir(_main_dir)
			for sub_folder in subDir_list:
				_sub_dir=os.path.join(_main_dir,sub_folder)
				pic_list=os.listdir(_sub_dir)
				for pic in pic_list:
					i+=1
					if (".jpg" in pic) and (search_text in pic.split("_")[0]):
						arr=pic.split("_")
						name=arr[0]
						temp_arr=[]
						r_department = base_folder.split("_")[1]

						for pp in pic_list:
							if get_image_name(pic) in pp[1]:
								temp_arr.append(pp)
						message_lists.append({
							"index":i,
							"r_department":r_department,
							"room":sub_folder,
							"name":name,
							"arr":temp_arr,
							"department":base_folder})
		message_lists=remove_duplicate_items(message_lists,"name")


	# 步驟(六)、設定分頁功能
	page_limit=10
	paginator_2 = MyPaginator(message_lists, page_limit) # 設定一頁要顯示幾筆
	total_2 = int(paginator_2.num_pages) # 將筆數計算總共有幾頁
	page_2 = request.GET.get('page', 1) # 接收使用者點選的頁碼
	contacts_2 = paginator_2.page(page_2) # (列表清單用變數) 回傳使用者點的頁碼，讓前台顯示 (取得第幾頁的內容再丟回contacts)
	message_lists_cut=contacts_2

	MEDIA_URL = settings.MEDIA_URL
	return render(request, """Health_Edu_search.html""",locals())
# @csrf_exempt
# def healthEdu_detail(request,main_item,sub_item):

# 	return render(request, """Health_Edu/{main_item}/{sub_item}""".fromat(),locals())

# @csrf_exempt
# def bread_pencil(request):
# 	return render(request, "bread_pencil.html",locals())

# @csrf_exempt
# def test(request, question_id):
#     return HttpResponse("You're looking at question %s." % question_id)

