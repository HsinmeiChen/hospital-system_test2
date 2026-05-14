# 定義共用「全域變數」連動 settings.py 設定，透過此 context_processors.py，傳遞到 HTML 模板（Template）
from django.conf import settings
from django.urls import resolve

# ■■■■■■■■■■■■■■■■■■■■■■■■■■ GA / GTM / OG-image ■■■■■■■■■■■■■■■■■■■■■■■■■■
def default_tracking_ids(request):
    # 先抓取網域，若沒有則預設空字串
    site_domain = getattr(settings, 'SITE_DOMAIN', '')
    path = request.path # 取得目前網址路徑

    if path.startswith('/specialty_medical/'): # 骨科微創中心
        default_og_image = f"{site_domain}/media/specialty_medical/ort/everan2.png"
    elif path.startswith('/specialty_health/'): # 健檢中心
        default_og_image = f"{site_domain}/media/specialty_health/everan2.png"
    elif path.startswith('/breast-care-center/'): # 乳房外科中心
        default_og_image = f"{site_domain}/media/Breast_Care_Center/everan2.png"
    elif path.startswith('/EECP/'): # EECP
        default_og_image = f"{site_domain}/media/EECP/EECP.png"
    else:
        # 主要官網 
        default_og_image = f"{site_domain}/Public/common/img/everan2.png"
    return {
        'SITE_DOMAIN': site_domain,
        'DEFAULT_GA_ID': getattr(settings, 'DEFAULT_GA_ID', 'G-GE353FP9KK'), # GA 追蹤碼
        'DEFAULT_GTM_ID': getattr(settings, 'DEFAULT_GTM_ID', 'GTM-TMHQ84N'), # GTM 追蹤碼
        'DEFAULT_OG_IMAGE': default_og_image, # 預設分享圖片
    }

# ■■■■■■■■■■■■■■■■■■■■■■■■■■ breadcrumb 麵包屑 ■■■■■■■■■■■■■■■■■■■■■■■■■■
def breadcrumb_processor(request):
    # 1. 取得當前網址路徑
    path_segments = request.path.strip("/").split("/")

    # 2. 定義網址片段與中文名稱的對應
    NAME_MAP = {
        "index": "本院首頁",
        "A000_news": "最新消息",
        "A000_reports": "媒體報導",
        "A000_closed_clinic": "停休診公告",
        "A000_video_message": "影音消息",
        "A000_medical_info": "醫療資訊", # 未開放
        "A000_medical_pages": "醫療專頁", # 醫療資訊-內頁
        "A001_department_overview": "科室總覽",
        "A001_department_part": "本科介紹", # 本科介紹-內頁 (帶參數)
        "A001_department_doctor": "專科醫師", # 醫師介紹-內頁 (帶參數)
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
        "A003_labor_clinical": "臨床檢驗採集衛教",
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
        "A005_ward_mes_1": "病人住院流程",
        "A005_ward_mes_2": "住院須知", # 未開放
        "A005_ward_mes_3": "病人出院流程",
        "A005_ward_mes_0": "病房費用",
        "A005_Diff_fee": "自付差額特材", # 未開放
        "A005_Self_fee": "自費項目", # 未開放
        "A006_Online_Booking_0": "網路掛號",
        "A006_Online_Booking_login": "民眾登入",
        "A006_Online_Booking_first": "初診資料填寫",
        "A006_Online_Booking_data": "預約資料記錄",
        "A006_Online_Booking_1": "選擇科別",
        "A006_Online_Booking_1_part": "科別預約",
        "A006_Online_Booking_2": "選擇醫師",
        "A006_Online_Booking_2_1": "醫師預約", # 帶醫師變數
        "A003_health_edu": "衛教園地",
        # "A007_Reserve_pre": "預約慢箋", # 頁面手動新增
        "specialty_medical": "骨科微創手術中心",
        "EECP": "EECP 體外反搏治療中心",
        "specialty_health": "健康管理中心",
        "breast-care-center": "全方位乳房中心",
    }
    # 3. 設定階層頁面 (父子頁面-3層以上要使用)
    PARENT_MAP = {
        # 急診醫學科
        "A003_ER": "A001_department_overview",
        "A003_ER_1": "A003_ER",
        "A003_ER_2": "A003_ER",
        "A003_Story_1": "A003_ER",
        "A003_Story_2": "A003_ER",

        # 網路掛號
        "A006_Online_Booking_1_part": "A006_Online_Booking_1",
        "A006_Online_Booking_2_1": "A006_Online_Booking_2",
    }

    breadcrumbs = []
    
    # 4. 定義子專案 (首頁不是 "/" 的獨立專案)
    MINI_SITES = {
        "breast-care-center": "首頁",
        "specialty_health": "首頁",
        "specialty_medical": "首頁",
        "EECP": "首頁"
    }

    if path_segments and path_segments[0]:
        first_segment = path_segments[0]
        
        # A. 如果是獨立子專案
        if first_segment in MINI_SITES:
            breadcrumbs.append({"name": MINI_SITES[first_segment], "url": f"/{first_segment}/"})
            url_accum = f"/{first_segment}/"
            
            # 排除首個子專案目錄，處理剩餘階層
            for p in path_segments[1:]:
                url_accum += p + "/"
                breadcrumbs.append({
                    "name": NAME_MAP.get(p, p.replace("-", " ").title()),
                    "url": url_accum
                })
        # B. 如果是標準網站頁面 (以本院首頁 "/" 為底)
        else:
            breadcrumbs.append({"name": "本院首頁", "url": "/"})
            current_p = path_segments[-1] # 目前最後一層
            
            # 建立層級鏈
            chain = []
            temp_p = current_p
            while temp_p:
                chain.insert(0, temp_p)
                # 1. 優先從 PARENT_MAP 取得 (手動覆蓋)
                next_p = PARENT_MAP.get(temp_p)
                
                # 2. 若無手動設定，則依規則動態判定
                if not next_p:
                    # [檢驗科] 第三層規則
                    if temp_p.startswith("A003_labor_clinical_in_"):
                        next_p = "A003_labor_clinical"
                    elif temp_p.startswith("A003_labor_clinical_3_"):
                        next_p = "A003_labor_clinical_3"
                    elif temp_p.startswith("A003_labor_clinical_4_"):
                        next_p = "A003_labor_clinical_4"
                    # [檢驗科] 通用父層規則 (只要是 A003_labor_ 開頭且不是檢驗科首頁，上一層就是檢驗科)
                    elif temp_p.startswith("A003_labor_") and temp_p != "A003_Laboratory":
                        next_p = "A003_Laboratory"
                    # [網路掛號] 通用父層規則
                    elif temp_p.startswith("A006_Online_Booking_") and temp_p != "A006_Online_Booking_0":
                        next_p = "A006_Online_Booking_0"
                
                temp_p = next_p

            # 轉換成麵包屑物件
            if len(path_segments) == 1 and (current_p in PARENT_MAP or current_p in NAME_MAP):
                 for p in chain:
                    url = f"/{p}/" if p != "index" else "/"
                    breadcrumbs.append({
                        "name": NAME_MAP.get(p, p.replace("-", " ").title()),
                        "url": url
                    })
            else:
                 url_accum = "/"
                 for p in path_segments:
                    url_accum += p + "/"
                    breadcrumbs.append({
                        "name": NAME_MAP.get(p, p.replace("-", " ").title()),
                        "url": url_accum
                    })
    else:
        # 首頁本身
        breadcrumbs.append({"name": "本院首頁", "url": "/"})
    return {"breadcrumbs": breadcrumbs}