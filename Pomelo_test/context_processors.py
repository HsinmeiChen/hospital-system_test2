# 定義共用「全域變數」連動 settings.py 設定，透過此 context_processors.py，傳遞到 HTML 模板（Template）
from django.conf import settings
from django.urls import resolve
import os
from Pomelo_API.views import _get_dept_dr_map

# ■■■■■■■■■■■■■■■■■■■■■■■■■■ GA / GTM / OG-image ■■■■■■■■■■■■■■■■■■■■■■■■■■
def default_tracking_ids(request):
	# 先抓取網域，若沒有則預設空字串
	site_domain = getattr(settings, 'SITE_DOMAIN', '')
	if not request or not hasattr(request, 'path'):
		return {
			'SITE_DOMAIN': site_domain,
			'DEFAULT_GA_ID': getattr(settings, 'DEFAULT_GA_ID', 'G-GE353FP9KK'), # GA 追蹤碼
			'DEFAULT_GTM_ID': getattr(settings, 'DEFAULT_GTM_ID', 'GTM-TMHQ84N'), # GTM 追蹤碼
			'DEFAULT_OG_IMAGE': f"{site_domain}/Public/common/img/everan2.jpg", # 預設分享圖片
		}

	path = request.path # 取得目前網址路徑

	if path.startswith('/specialty_medical/'): # 骨科微創中心
		default_og_image = f"{site_domain}/media/specialty_medical/ort/everan2.png"
	elif path.startswith('/specialty_health/'): # 健檢中心
		default_og_image = f"{site_domain}/media/specialty_health/everan2.png"
	elif path.startswith('/breast-care-center/'): # 乳房外科中心
		default_og_image = f"{site_domain}/media/Breast_Care_Center/everan2.png"
	elif path.startswith('/EECP/'): # EECP
		default_og_image = f"{site_domain}/media/EECP/EECP.png"
	elif path.startswith('/neuro-center/'): # 神經醫學中心
		default_og_image = f"{site_domain}/media/neuro_center/og-neuro-center.jpg"
	elif path.startswith('/cardio-center/'): # 心血管中心
		default_og_image = f"{site_domain}/media/cardio_center/og_cardio_center.jpg"
	else:
		# 主要官網 
		default_og_image = f"{site_domain}/Public/common/img/everan2.jpg"
	return {
		'SITE_DOMAIN': site_domain,
		'DEFAULT_GA_ID': getattr(settings, 'DEFAULT_GA_ID', 'G-GE353FP9KK'), # GA 追蹤碼
		'DEFAULT_GTM_ID': getattr(settings, 'DEFAULT_GTM_ID', 'GTM-TMHQ84N'), # GTM 追蹤碼
		'DEFAULT_OG_IMAGE': default_og_image, # 預設分享圖片
	}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■ breadcrumb 麵包屑 ■■■■■■■■■■■■■■■■■■■■■■■■■■
def get_dynamic_name(segment, request):
	"""根據 URL 參數動態尋找科別或醫師名稱"""
	mapping = _get_dept_dr_map() # 取得快取

	# 如果 segment 是 1_1 這種科別 ID
	if segment in mapping['depts']:
		return mapping['depts'][segment]['name']

	# 如果 segment 是 HA00086 這種醫師 ID
	if segment in mapping['doctors']:
		# 取得醫師名稱 (從檔案名 D000_1_姓名_ID.txt 中抓取)
		return mapping['doctors'][segment]['filename'].split("_")[2]

	name_val = None
	try:
		from django.conf import settings
		pathC = os.path.join(settings.MEDIA_ROOT, 'department')
		
		# 1. 處理【科別介紹頁面】
		if segment == "A001_department_part":
			path_id = request.GET.get("open_info_name") or request.GET.get("open_info_path") or request.session.get("path")
			
			# 如果 path_id 是檔名格式 (如 D000_1_李育嘉_HA00086.txt)，提取醫師 ID
			if path_id and "D000" in path_id and "_" in path_id:
				parts = path_id.split("_")
				if len(parts) >= 4:
					dr_real_id = parts[3].replace(".txt", "")
					if dr_real_id in mapping['doctors']:
						path_id = dr_real_id

			if path_id:
				# --- [新增：優先從快取對照表中直接抓取] ---
				# 如果是醫師 ID (如 HA00086)，直接從醫師對照表抓科別名稱
				if path_id in mapping['doctors']:
					name_val = mapping['doctors'][path_id]['dept_name']
				# 如果是科別 ID (如 1_1)，直接從科別對照表抓名稱
				elif path_id in mapping['depts']:
				   name_val = mapping['depts'][path_id]['name']
				# --- [備案：如果快取找不到，才跑原本的目錄掃描 (保持相容性)] ---
				if not name_val and "_" in path_id:
					parts = path_id.split("_")
					pathP, pathD = path_id.split("_")[0], path_id.split("_")[1]
					for d000 in os.listdir(pathC):
						if "D000" in d000 and pathP == d000.split("_")[1]:
							target_dir = os.path.join(pathC, d000)
							for sub_dir in os.listdir(target_dir):
								if pathD == sub_dir.split("_")[0]:
									name_val = sub_dir.split("_")[1]
									break
								
		# 2. 處理【專科醫師介紹頁面】
		elif segment == "A001_department_doctor":
			pass

		# 3. 處理【網路掛號 - 科別預約】
		elif segment == "A006_Online_Booking_1_part":
			# 直接從網址參數抓取科別名稱
			name_val = request.GET.get("A006_sename")
			
		# 4. 處理【網路掛號 - 醫師預約】
		elif segment == "A006_Online_Booking_2_1":
			# (A) 優先從網址抓姓名參數 (效能最快)
			name_val = request.GET.get("A006_drname") or request.GET.get("drname")
			
			# (B) 如果網址沒帶姓名，則透過 userid (醫師編號) 去掃描尋找
			if not name_val:
				userid = request.GET.get("A006_userid")
				sename = request.GET.get("A006_sename") # 科別名稱 (如：骨科)
				if userid:
					found = False
					for d000 in os.listdir(pathC):
						if "D000" in d000:
							target_dir = os.path.join(pathC, d000)
							for sub_dir in os.listdir(target_dir):
								# 效能優化：優先搜尋名稱相符的科別資料夾
								if sename and sename in sub_dir:
									doctor_dir = os.path.join(target_dir, sub_dir)
									if os.path.isdir(doctor_dir):
										for f in os.listdir(doctor_dir):
											if userid in f and f.endswith(".txt"):
												f_parts = f.split("_")
												if len(f_parts) >= 3:
													name_val = f_parts[2] # 取得姓名與職稱
													found = True
													break
								if found: break
							if found: break
			
	except:
		pass 
	return name_val



def breadcrumb_processor(request):
	# 1. 取得當前網址路徑
	if not request or not hasattr(request, 'path'):
		return {
			"breadcrumbs": [],
			"side_doctors": [],
			"side_dept_name": "",
			"side_dept_url": "",
			"current_dr_id": None
		}
	path_segments = request.path.strip("/").split("/")

	# 移除分頁路徑片段，避免影響麵包屑生成
	if len(path_segments) >= 2 and path_segments[-2] == 'page' and path_segments[-1].isdigit():
		path_segments = path_segments[:-2]

	# 2. 定義網址片段與中文名稱的對應
	NAME_MAP = {
		"index": "本院首頁",
		"A000_news": "最新消息",
		"A000_reports": "媒體報導",
		"A000_closed_clinic": "停休診公告",
		"A000_video_message": "影音消息",
		"A000_medical_info": "醫療資訊",
		"A000_medical_pages": "醫療專頁", # 醫療資訊-內頁
		"A001_department_overview": "科室總覽",
		"A001_department_part": "本科介紹", # 本科介紹-內頁 (目前帶各科變數，若失敗改帶本科介紹)
		"A001_department_doctor": "專科醫師", # 醫師介紹-內頁 (目前帶各醫師變數，若失敗改帶專科醫師)
		"A001_dr_search": "醫師查詢",
		"A002_consultation_progress": "看診進度",
		"A002_which_disease": "我該看哪一科",
		"A002_registration_notice": "掛號須知",
		"A002_clinic_time": "門診時刻表",
		"A002_payment_machine": "繳費機介紹", # 未開放
		"A002_self_service": "自助掛號機介紹",
		"A002_data_apply": "資料申請",
		"A003_Medical_Support": "支援單位總覽",
		"A102_Safe_ISMS": "資通安全政策聲明",
		"A003_ER": "急診醫學科",
		"A003_ER_1": "醫師陣容",
		"A003_ER_2": "檢傷流程",
		"A003_AED": "AED 介紹",
		"A003_AED_1": "AED 新聞媒體、相關影音",
		"A003_Story_1": "民眾感謝",
		"A003_Story_2": "定期訓練",
		# 檢驗科子頁面
		"A003_Laboratory": "檢驗科",
		"A003_Laboratory_1": "最新公告", # asp
		"A003_Laboratory_2": "公正性及保密承諾",
		"A003_Laboratory_3": "抱怨程序", # asp
		"A003_Laboratory_4": "聯絡我們",
		"A003_labor_blood": "門診抽血",
		"A003_labor_blood_2": "領取驗尿及糞便檢體容器",
		"A003_labor_blood_3": "心電圖及肺功能檢查流程",
		"A003_labor_clinical": "臨床檢體採集衛教",
		"A003_labor_clinical_1": "臨床採檢容器說明",
		"A003_labor_clinical_2": "臨床採檢前作業流程",
		"A003_labor_clinical_3": "臨床檢體採集原則",
		"A003_labor_clinical_3_3c": "特殊免疫檢驗採集 (Cold agglutinin、Cryoglobulin)",
		"A003_labor_clinical_3_art": "動脈血檢體採集",
		"A003_labor_clinical_3_baby": "新生兒腳跟血毛細管採集",
		"A003_labor_clinical_3_blood": "血液檢體採集前評估",
		"A003_labor_clinical_3_cav": "體腔積液採集(胸水、腹水等)",
		"A003_labor_clinical_3_csf": "腦脊髓液 (CSF) 檢體採集",
		"A003_labor_clinical_3_dung": "糞便檢體採集",
		"A003_labor_clinical_3_ra": "QuantiFERON (IGRA) 檢體採集",
		"A003_labor_clinical_3_phlegm": "痰液檢體採集",
		"A003_labor_clinical_3_prepare": "輸備血檢體採集",
		"A003_labor_clinical_3_respiratory": "呼吸道檢體採集",
		"A003_labor_clinical_3_semen": "精液檢體採集",
		"A003_labor_clinical_3_solid": "血液凝固檢驗檢體採檢",
		"A003_labor_clinical_3_sugar": "快速血糖檢驗指尖血採集",
		"A003_labor_clinical_3_tract": "胃腸道檢體採集",
		"A003_labor_clinical_3_urine": "尿液檢體採集",
		"A003_labor_clinical_3_vein": "靜脈血檢體採集",
		"A003_labor_clinical_3_wine": "酒精濃度 (Alcohol) 檢體採集",
		"A003_labor_clinical_4": "微生物培養採檢須知",
		"A003_labor_clinical_4_abscess": "一般細菌培養(膿瘍檢體採集)",
		"A003_labor_clinical_4_bf": "一般細菌培養(體液檢體採集)",
		"A003_labor_clinical_4_bottle": "血瓶檢體採集",
		"A003_labor_clinical_4_collection": "細菌培養檢體採集方法須知",
		"A003_labor_clinical_4_dung": "糞便培養檢體採集",
		"A003_labor_clinical_4_eye": "眼睛檢體採集",
		"A003_labor_clinical_4_respiratory": "一般細菌培養(呼吸道檢體採集)",
		"A003_labor_clinical_4_urine": "尿液培養檢體採集",
		"A003_labor_clinical_5": "臨床檢體共通退件原則",
		"A003_labor_clinical_6": "臨床檢驗服務項目", # asp
		"A003_labor_clinical_7": "臨床檢體加作及複驗",
		"A003_labor_clinical_8": "臨床危險值及重要異常值通報",
		"A003_labor_clinical_9": "臨床報告單位換算", # asp
		"A003_labor_clinical_in_b": "抽血注意事項",
		"A003_labor_clinical_in_du": "糞便採檢注意事項",
		"A003_labor_clinical_in_glu": "口服葡萄糖耐受性檢驗試驗採檢須知",
		"A003_labor_clinical_in_ig": "IGRA 採檢及檢體前處理須知",
		"A003_labor_clinical_in_occ": "免疫糞便定量潛血檢查",
		"A003_labor_clinical_in_pin": "蟯蟲檢測採檢注意事項",
		"A003_labor_clinical_in_sem": "精液分析採檢注意事項",
		"A003_labor_clinical_in_spu": "痰液培養採檢注意事項",
		"A003_labor_clinical_in_third": "碳十三呼氣檢查採檢須知",
		"A003_labor_clinical_in_urine": "尿液採檢注意事項",
		"A003_labor_Genetic": "基因檢測檢體採集及送檢注意事項",
		"A003_labor_Genetic_1": "檢體容器說明", # 未開放
		"A003_labor_pathology": "病理檢體採集及包裝注意事項",
		"A003_labor_pathology_1": "病人辨識",
		"A003_labor_pathology_2": "細胞病理檢體採集注意事項",
		"A003_labor_pathology_3": "細胞病理診斷抹片前處理需求",
		"A003_labor_pathology_4": "細胞學檢體容器說明", # 未開放
		"A003_labor_pathology_5": "病理服務項目",
		"A004_hos_intro": "長安簡介",
		"A004_hos_traffic_info": "交通資訊",
		"A004_hos_lost_info": "失物招領",
		"A004_contact_us": "意見反映",
		"A005_ward_mes_1": "病人住院流程",
		"A005_ward_mes_2": "住院須知", # 未開放
		"A005_ward_mes_3": "病人出院流程",
		"A005_ward_mes_0": "病房費用",
		"A005_Diff_fee": "自付差額特材", # 未開放
		"A005_Self_fee": "自費項目", # 未開放
		"A006_Online_Booking_0": "網路掛號",
		"A006_Online_Booking_login": "民眾登入",
		"A006_Online_Booking_first": "初診資料填寫",
		"A006_Online_Booking_check": "確認預約資料",
		"A006_Online_Booking_data": "掛號查詢與取消",
		"A006_Online_Booking_1": "依科別掛號",
		"A006_Online_Booking_1_part": "科別預約",
		"A006_Online_Booking_2": "依醫師掛號",
		"A006_Online_Booking_2_1": "醫師預約", # 帶醫師變數
		"A003_health_edu": "衛教園地",
		# "A007_Reserve_pre": "預約慢箋", # 頁面手動新增
		"specialty_medical": "骨科微創手術中心",
		"EECP": "EECP 體外反搏治療中心",
		"specialty_health": "健康管理中心",
		"breast-care-center": "全方位乳房中心",
	}
	# 3. 設定階層頁面
	PARENT_MAP = {
		"A003_ER": "A001_department_overview",
		"A003_ER_1": "A003_ER",
		"A003_ER_2": "A003_ER",
		"A003_Story_1": "A003_ER",
		"A003_Story_2": "A003_ER",
		"A006_Online_Booking_1_part": "A006_Online_Booking_1",
		"A006_Online_Booking_2_1": "A006_Online_Booking_2",
	}

	breadcrumbs = []
	side_doctors = [] 
	side_dept_name = "" 
	side_dept_url = "" 
	current_dr_id = None

	# --- [側邊選單醫師列表邏輯] ---
	if any(seg in path_segments for seg in ["A001_department_part", "A001_department_doctor", "department", "doctor"]):
		try:
			mapping = _get_dept_dr_map()
			path_id = request.GET.get("open_info_name") or request.GET.get("open_info_path") or request.session.get("path")
			
			# 優先嘗試從新網址路徑中解析科別或醫師 ID
			if len(path_segments) >= 3 and path_segments[0] == "A001_department_doctor":
				dept_en_from_url = path_segments[1]
				dr_id_from_url = path_segments[2]
				# 優先使用「科別英文_醫師ID」組合鍵比對，避免跨科別同工號衝突
				combo_key = f"{dept_en_from_url}_{dr_id_from_url}"
				if combo_key in mapping['doctors']:
					path_id = combo_key
				elif dr_id_from_url in mapping['doctors']:
					path_id = dr_id_from_url
			elif len(path_segments) >= 2 and path_segments[0] == "A001_department_overview":
				dept_en_from_url = path_segments[1]
				if dept_en_from_url in mapping['dept_en_to_id']:
					path_id = mapping['dept_en_to_id'][dept_en_from_url]

			# 如果 path_id 是檔名格式 (如 D000_1_李育嘉_HA00086.txt)，提取醫師 ID
			if path_id and "D000" in path_id and "_" in path_id:
				parts = path_id.split("_")
				if len(parts) >= 4:
					dr_real_id = parts[3].replace(".txt", "")
					if dr_real_id in mapping['doctors']:
						path_id = dr_real_id

			if path_id:
				dept_id = None
				if path_id in mapping['doctors']:
					dept_id = mapping['doctors'][path_id]['path_id'].split("_")[0] + "_" + mapping['doctors'][path_id]['path_id'].split("_")[1]
					current_dr_id = mapping['doctors'][path_id]['path_id'].split("_")[2] # 使用內部序號作為 active 判斷
				elif path_id in mapping['depts']:
					dept_id = path_id
					
				if dept_id and dept_id in mapping['depts']:
					dept_info = mapping['depts'][dept_id]
					side_dept_name = dept_info['name']
					side_dept_url = f"/A001_department_overview/{dept_info['en']}/"
					
					doctor_dir = dept_info['full_path']
					if os.path.isdir(doctor_dir):
						for f in os.listdir(doctor_dir):
							if f.startswith("D000") and f.endswith(".txt"):
								f_parts = f.split("_")
								if len(f_parts) >= 4:
									# 以空格拆分姓名與職稱
									name_parts = f_parts[2].split(' ', 1)
									dr_name = name_parts[0]
									dr_title = name_parts[1] if len(name_parts) > 1 else "醫師介紹"
									dr_real_id = f_parts[3].replace('.txt', '')
									
									side_doctors.append({
										'sort_idx': int(f_parts[1]),
										'full_name': f_parts[2],
										'dr_name': dr_name,
										'dr_title': dr_title, 
										'dr_id': f_parts[1], # 保留原始邏輯的 active 判斷用序號
										'url': f"/A001_department_doctor/{dept_info['en']}/{dr_real_id}/"
									})
						# 依照序號排序
						side_doctors.sort(key=lambda x: x['sort_idx'])
		except:
			pass

	# 4. 定義子專案
	MINI_SITES = {
		"breast-care-center": "首頁",
		"specialty_health": "首頁",
		"specialty_medical": "首頁",
		"EECP": "首頁"
	}

	# --- [麵包屑生成邏輯] ---
	if path_segments and path_segments[0]:
		first_segment = path_segments[0]
		if first_segment in MINI_SITES:
			breadcrumbs.append({"name": MINI_SITES[first_segment], "url": f"/{first_segment}/"})
			url_accum = f"/{first_segment}/"
			for p in path_segments[1:]:
				url_accum += p + "/"
				breadcrumbs.append({
					"name": NAME_MAP.get(p, p.replace("-", " ").title()),
					"url": url_accum
				})
		else:
			breadcrumbs.append({"name": "本院首頁", "url": "/"})
			current_p = path_segments[-1]
			chain = []
			temp_p = current_p
			while temp_p:
				chain.insert(0, temp_p)
				next_p = PARENT_MAP.get(temp_p)
				if not next_p:
					if temp_p.startswith("A003_labor_clinical_in_"): next_p = "A003_labor_clinical"
					elif temp_p.startswith("A003_labor_clinical_3_"): next_p = "A003_labor_clinical_3"
					elif temp_p.startswith("A003_labor_clinical_4_"): next_p = "A003_labor_clinical_4"
					elif temp_p.startswith("A003_labor_") and temp_p != "A003_Laboratory": next_p = "A003_Laboratory"
					elif temp_p.startswith("A006_Online_Booking_") and temp_p != "A006_Online_Booking_0": next_p = "A006_Online_Booking_0"
				temp_p = next_p

			# --------- 處理舊網址、分享連結 start ---------
			if len(path_segments) == 1 and (current_p in PARENT_MAP or current_p in NAME_MAP):
				for p in chain:
					url = f"/{p}/" if p != "index" else "/"
					display_name = NAME_MAP.get(p, p.replace("-", " ").title())
					if p == "A001_department_doctor":
						dept_name = get_dynamic_name("A001_department_part", request)
						if dept_name:
							path_id = request.GET.get("open_info_name") or request.GET.get("open_info_path") or request.session.get("path")

							# 解析醫師 ID 以取得正確的科別 ID (dept_id)
							mapping = _get_dept_dr_map()
							if path_id in mapping['doctors']:
								path_id = mapping['doctors'][path_id]['path_id'] # 轉為 1_1_1 格式

							if path_id and path_id.count("_") >= 2:
								dept_id = "_".join(path_id.split("_")[:2])
								breadcrumbs.append({"name": dept_name, "url": f"/A001_department_overview/{dept_id}/"})
					dynamic_name = get_dynamic_name(p, request)
					if dynamic_name: display_name = dynamic_name
					breadcrumbs.append({"name": display_name, "url": url})
					# --------- 處理舊網址、分享連結 End ---------
			
			# --------- 處理新網址 start ---------
			else:
				if path_segments[0] == "A001_department_doctor" and len(path_segments) >= 3:
					dept_en = path_segments[1]
					dr_id = path_segments[2]
					mapping = _get_dept_dr_map()
					
					# 1. 抓取科別名稱並建立連結
					dept_name = dept_en
					if dept_en in mapping['dept_en_to_id']:
						dept_id = mapping['dept_en_to_id'][dept_en]
						dept_name = mapping['depts'][dept_id]['name']
					
					breadcrumbs.append({"name": dept_name, "url": f"/A001_department_overview/{dept_en}/"})
					
					# 2. 抓取醫師名稱並建立連結
					dr_name = dr_id
					combo_key = f"{dept_en}_{dr_id}"
					if combo_key in mapping['doctors']:
						dr_name = mapping['doctors'][combo_key]['filename'].split("_")[2]
					elif dr_id in mapping['doctors']:
						dr_name = mapping['doctors'][dr_id]['filename'].split("_")[2] # 例如: "李育嘉 主治醫師"
					
					breadcrumbs.append({"name": dr_name, "url": f"/A001_department_doctor/{dept_en}/{dr_id}/"})
					
				elif path_segments[0] == "A001_department_overview" and len(path_segments) >= 2:
					dept_en = path_segments[1]
					mapping = _get_dept_dr_map()
					
					# 增加科室總覽節點
					breadcrumbs.append({"name": "科室總覽", "url": "/A001_department_overview/"})

					# 抓取科別名稱並建立連結
					dept_name = dept_en
					if dept_en in mapping['dept_en_to_id']:
						dept_id = mapping['dept_en_to_id'][dept_en]
						dept_name = mapping['depts'][dept_id]['name']
						
					breadcrumbs.append({"name": dept_name, "url": f"/A001_department_overview/{dept_en}/"})

				elif path_segments[0] == "A006_Online_Booking_2_1" and len(path_segments) >= 3:
					dept_en = path_segments[1]
					dr_id = path_segments[2]
					
					# 建立固定的 A006 層級
					breadcrumbs.append({"name": "網路掛號", "url": "/A006_Online_Booking_0/"})
					breadcrumbs.append({"name": "依醫師掛號", "url": "/A006_Online_Booking_2/"})
					
					# 動態抓取醫師名稱
					mapping = _get_dept_dr_map()
					dr_name = "醫師預約"
					combo_key = f"{dept_en}_{dr_id}"
					if combo_key in mapping['doctors']:
						dr_name = mapping['doctors'][combo_key]['filename'].split("_")[2]
					elif dr_id in mapping['doctors']:
						dr_name = mapping['doctors'][dr_id]['filename'].split("_")[2] # 例如: "李育嘉 主治醫師"
						
					breadcrumbs.append({"name": dr_name, "url": f"/A006_Online_Booking_2_1/{dept_en}/{dr_id}/"})

				elif path_segments[0] == "A006_Online_Booking_1_part" and len(path_segments) >= 2:
					dept_en = path_segments[1]
					
					breadcrumbs.append({"name": "網路掛號", "url": "/A006_Online_Booking_0/"})
					breadcrumbs.append({"name": "依科別掛號", "url": "/A006_Online_Booking_1/"})
					
					mapping = _get_dept_dr_map()
					dept_name = dept_en
					if dept_en in mapping['dept_en_to_id']:
						dept_id = mapping['dept_en_to_id'][dept_en]
						dept_name = mapping['depts'][dept_id]['name']
						
					breadcrumbs.append({"name": dept_name, "url": f"/A006_Online_Booking_1_part/{dept_en}/"})

				elif path_segments[0] == "A003_health_edu" and len(path_segments) >= 2:
					breadcrumbs.append({"name": "衛教園地", "url": "/A003_health_edu/"})
					sub_item_en = path_segments[1]
					if sub_item_en != "search":
						sub_chinese = sub_item_en
						main_item = None
						sub_item = None
						_base_dir = os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc')
						if os.path.exists(_base_dir):
							for main_dir in os.listdir(_base_dir):
								if os.path.isdir(os.path.join(_base_dir, main_dir)):
									for sub_dir in os.listdir(os.path.join(_base_dir, main_dir)):
										if "_" in sub_dir:
											parts = sub_dir.split("_")
											if len(parts) > 1 and parts[1].lower() == sub_item_en.lower():
												sub_chinese = parts[0]
												main_item = main_dir
												sub_item = sub_dir
												break
						breadcrumbs.append({"name": sub_chinese, "url": f"/A003_health_edu/{sub_item_en}/"})
						if len(path_segments) >= 3:
							title_segment = path_segments[2]
							display_title = title_segment
							if main_item and sub_item:
								_dir = os.path.join(settings.MEDIA_ROOT, 'health_edu', 'Doc', main_item, sub_item)
								if os.path.exists(_dir):
									import hashlib
									# 優先以 hash 值比對
									for f in os.listdir(_dir):
										if f.lower().endswith('.jpg') and '_' in f:
											 prefix = f.split('_')[0]
											 h = hashlib.md5(prefix.encode('utf-8')).hexdigest()[:8]
											 if h == title_segment:
												 display_title = prefix
												 break
									# 備案：若傳入的就是原中文 (相容舊網址)
									if display_title == title_segment:
										 for f in os.listdir(_dir):
											 if f.lower().endswith('.jpg') and f.startswith(title_segment + '_'):
												 display_title = title_segment
												 break
							breadcrumbs.append({"name": display_title, "url": f"/A003_health_edu/{sub_item_en}/{title_segment}/"})

				else:
					url_accum = "/"
					for p in path_segments:
						display_name = NAME_MAP.get(p, p.replace("-", " ").title())
						url_accum += p + "/"
						actual_url = url_accum

						if p == "A001_dr_search":
							display_name = "醫師查詢"

						dynamic_name = get_dynamic_name(p, request)
						if dynamic_name: display_name = dynamic_name
						breadcrumbs.append({"name": display_name, "url": actual_url})
			# --------- 處理新網址 End ---------

	else:
		breadcrumbs.append({"name": "本院首頁", "url": "/"})

	# --- [唯一的 return：位於函式最末端] ---
	return {
		"breadcrumbs": breadcrumbs,
		"side_doctors": side_doctors,
		"side_dept_name": side_dept_name,
		"side_dept_url": side_dept_url,
		"current_dr_id": current_dr_id
	}