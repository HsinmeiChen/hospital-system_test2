from django.contrib.sitemaps import Sitemap
from django.urls import reverse
import os
import glob
from django.conf import settings
import re

class ForceDomainSitemapMixin:
    """
    這個 Mixin 強制 Sitemap 輸出 HTTPS 以及指定的網域名稱，
    避免 Django 去抓資料庫裡預設的 example.com 導致 Google Search Console 報錯。
    """
    protocol = 'https'

    def get_urls(self, page=1, site=None, protocol=None):
        class FakeSite:
            domain = 'web.everanhospital.com.tw'
            name = '長安醫院'
        return super().get_urls(page=page, site=FakeSite(), protocol=self.protocol)

class StaticSitemap(ForceDomainSitemapMixin, Sitemap):
    """
    靜態核心網頁的 Sitemap (包含所有特色醫療中心首頁及常用服務)
    """
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        # 這裡放置所有定義在 urls.py 中的具名網址 (name='...')
        # 如果有些網址沒有 name，我們就直接回傳字串路徑
        return [
            'index',
            'common_captcha_img',
        # === 主網站主要服務 ===
            '/A001_department_overview/', '/A001_dr_search/',
            '/A002_consultation_progress/', '/A002_registration_notice/', 
            '/A002_which_disease/', '/A002_clinic_time/', '/A002_self_service/', '/A002_data_apply/',
            '/A003_Medical_Support/', '/A003_ER/', '/A003_AED/', '/A003_Laboratory/', 
            '/A003_health_edu/', '/A003_labor_blood/', '/A003_labor_clinical/', '/A003_labor_pathology/',
            '/A004_hos_intro/', '/A004_hos_traffic_info/', '/A004_hos_lost_info/', '/A004_contact_us/',
            '/A005_ward_mes_0/', '/A005_ward_mes_1/', '/A005_ward_mes_3/', '/A005_ward_mes_4/', '/A005_Self_fee/',
            '/A006_Online_Booking_0/', '/A006_Online_Booking_1/', '/A006_Online_Booking_2/',
            '/A100_search_sename/', '/A101_search_bed/', '/A102_Safe_ISMS/', '/A103_search_ITH_bed/',
            
            # === 各大特色醫療中心 (首頁、關於我們、各類清單頁、聯絡我們) ===
            '/cardio-center/', '/cardio-center/about/', '/cardio-center/news/', '/cardio-center/media/', 
            '/cardio-center/film/', '/cardio-center/doctor/', '/cardio-center/treatment/', '/cardio-center/edu/', '/cardio-center/contact/',
            
            '/breast-care-center/', '/breast-care-center/breast-about/', '/breast-care-center/breast-news/', '/breast-care-center/breast-media/',
            '/breast-care-center/breast-film/', '/breast-care-center/breast-doctor/', '/breast-care-center/breast-treatment/', '/breast-care-center/breast-edu/', '/breast-care-center/contact/',
            
            '/neuro-center/', '/neuro-center/neuro-about/', '/neuro-center/neuro-news/', '/neuro-center/neuro-media/',
            '/neuro-center/neuro-film/', '/neuro-center/neuro-doctor/', '/neuro-center/neuro-treatment/', '/neuro-center/neuro-edu/', '/neuro-center/contact/',
            
            '/specialty_health/', '/specialty_health/health-about/', '/specialty_health/health-news/', '/specialty_health/health-media/',
            '/specialty_health/health-health-film/', '/specialty_health/health-doctor/', '/specialty_health/health-treatment/', '/specialty_health/health-health-edu/', '/specialty_health/contact/',
            
            '/specialty_medical/', '/specialty_medical/medical-about/', '/specialty_medical/news/', '/specialty_medical/media/',
            '/specialty_medical/film/', '/specialty_medical/doctor/', '/specialty_medical/treatment/', '/specialty_medical/edu/', '/specialty_medical/contact/',
            
            '/EECP/', '/EECP/eecp-about/', '/EECP/eecp-news/', '/EECP/eecp-media/',
            '/EECP/eecp-film/', '/EECP/eecp-doctor/', '/EECP/eecp-treatment/', '/EECP/eecp-edu/', '/EECP/contact/',
        ]

    def location(self, item):
        # 如果是直接給的字串路徑，就直接回傳
        if item.startswith('/'):
            return item
        # 如果是 urls.py 裡面有 name= 的網址，就用 reverse 去解析
        try:
            return reverse(item)
        except:
            return f"/{item}/"

class TxtDynamicSitemap(ForceDomainSitemapMixin, Sitemap):
    """
    動態掃描 TXT 資料夾並產生網址的 Sitemap 類別。
    """
    priority = 0.6
    changefreq = 'weekly'

    def __init__(self, dir_path, url_name_or_prefix, is_reverse=True):
        """
        :param dir_path: 要掃描的資料夾路徑 (相對於 MEDIA_ROOT，例如 'news_2')
        :param url_name_or_prefix: 對應的 URL 名稱 (如果有定義 name)，或是固定的網址前綴 (例如 '/A000_news/')
        :param is_reverse: 是否使用 reverse() 解析。若為 False，則直接將前綴與檔名組合。
        """
        self.dir_path = os.path.join(settings.MEDIA_ROOT, dir_path)
        self.url_name_or_prefix = url_name_or_prefix
        self.is_reverse = is_reverse

    def items(self):
        slugs = []
        if os.path.exists(self.dir_path):
            # 掃描資料夾下所有的 .txt 檔案
            txt_files = glob.glob(os.path.join(self.dir_path, '*.txt'))
            for f in txt_files:
                basename = os.path.basename(f)
                slug = os.path.splitext(basename)[0] # 去除副檔名
                # 若您的檔名需要特殊處理(例如過濾掉不是英數字的)，可以在此過濾
                slugs.append(slug)
        return slugs

    def location(self, slug):
        if self.is_reverse:
            try:
                return reverse(self.url_name_or_prefix, kwargs={'slug': slug})
            except Exception as e:
                # 若 reverse 失敗，退回到直接組合字串 (備案)
                return f"/{self.url_name_or_prefix}/{slug}/"
        else:
            return f"{self.url_name_or_prefix}{slug}/"

# 在這裡定義所有動態掃描的資料夾與網址對應關係
# 格式: TxtDynamicSitemap('資料夾相對路徑 (相對於 MEDIA_ROOT)', 'URL前綴', is_reverse=False)
# 備註: 使用 is_reverse=False 可以避免 Django Reverse Match Error，最為安全穩健。
sitemaps_dict = {
    'static': StaticSitemap,
    
    # === 主網站 ===
    'main_news': TxtDynamicSitemap('news_2', '/A000_news/', is_reverse=False),
    
    # === 心血管中心 (Cardio Center) ===
    'cardio_news': TxtDynamicSitemap('news_2', '/cardio-center/news/', is_reverse=False),
    'cardio_edu': TxtDynamicSitemap('cardio_center/cardio_edu', '/cardio-center/edu/', is_reverse=False),
    'cardio_treatment': TxtDynamicSitemap('cardio_center/treatment', '/cardio-center/treatment/', is_reverse=False),
    
    # === 乳房中心 (Breast Care Center) ===
    'breast_news': TxtDynamicSitemap('news_2', '/breast-care-center/breast-news/', is_reverse=False),
    'breast_edu': TxtDynamicSitemap('Breast_Care_Center/breast-edu', '/breast-care-center/breast-edu/', is_reverse=False),
    'breast_treatment': TxtDynamicSitemap('Breast_Care_Center/treatment', '/breast-care-center/breast-treatment/', is_reverse=False),
    
    # === 神經醫學中心 (Neurology Center) ===
    'neuro_news': TxtDynamicSitemap('news_2', '/neuro-center/neuro-news/', is_reverse=False),
    'neuro_edu': TxtDynamicSitemap('Neurology_Center/neuro-edu', '/neuro-center/neuro-edu/', is_reverse=False),
    'neuro_treatment': TxtDynamicSitemap('Neurology_Center/treatment', '/neuro-center/neuro-treatment/', is_reverse=False),
    
    # === 健康管理中心 (Specialty Health) ===
    'health_news': TxtDynamicSitemap('news_2', '/specialty_health/health-news/', is_reverse=False),
    'health_treatment': TxtDynamicSitemap('specialty_health/treatment', '/specialty_health/health-treatment/', is_reverse=False),
    
    # === 骨科微創手術中心 (Specialty Medical) ===
    'ortho_news': TxtDynamicSitemap('news_2', '/specialty_medical/news/', is_reverse=False),
    'ortho_edu': TxtDynamicSitemap('specialty_medical/medical_edu', '/specialty_medical/edu/', is_reverse=False),
    'ortho_treatment': TxtDynamicSitemap('specialty_medical/treatment', '/specialty_medical/treatment/', is_reverse=False),
    
    # === EECP 體外反搏治療中心 ===
    'eecp_news': TxtDynamicSitemap('news_2', '/EECP/eecp-news/', is_reverse=False),
    'eecp_edu': TxtDynamicSitemap('EECP/eecp-edu', '/EECP/eecp-edu/', is_reverse=False),
}

try:
    from Pomelo_API.views import _get_dept_dr_map
    class DoctorSitemap(ForceDomainSitemapMixin, Sitemap):
        """
        醫師介紹頁的動態 Sitemap
        掃描 HIS 同步下來的醫師資料夾，並產生類似 /A001_department_doctor/Orthopedic/HA00504/ 的專屬網址。
        """
        priority = 0.7
        changefreq = 'weekly'

        def items(self):
            mapping = _get_dept_dr_map()
            doctors = mapping.get('doctors', {})
            # doctors dict 裡面一個醫師可能會有 3 個 key (dr_id, path_id, dept_en_dr_id)
            # 我們使用 set 或是依賴 dict 值本身的唯一性來避免重複
            unique_docs = {}
            for doc in doctors.values():
                unique_key = f"{doc['dept_en']}_{doc['id']}"
                unique_docs[unique_key] = doc
            return list(unique_docs.values())

        def location(self, doc):
            # doc 是 items() 傳回來的 dict
            dept_en = doc.get('dept_en', '')
            dr_id = doc.get('id', '')
            return f"/A001_department_doctor/{dept_en}/{dr_id}/"
            
    # 將醫師 Sitemap 加進清單
    sitemaps_dict['doctors'] = DoctorSitemap
except ImportError:
    # 避免系統在尚未加載 Pomelo_API 時報錯
    pass

