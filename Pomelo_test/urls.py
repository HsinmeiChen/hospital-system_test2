"""Pomelo_test URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
	https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
	1. Add an import:  from my_app import views
	2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
	1. Add an import:  from other_app.views import Home
	2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
	1. Import the include() function: from django.urls import include, path
	2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include,re_path, path
from django.views.generic import TemplateView
import Pomelo_API.views as pomelo_views   # 若程式都在同支 view.py，就不用再 import 新的
import Pomelo_test.utils as pomelo_test_utils


from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib.sitemaps.views import sitemap
from Pomelo_test.sitemaps import sitemaps_dict


# URL路徑 (指可設定網址名稱；若沒有定義參數，可用 re_path 路由)
urlpatterns = [
	path('sitemap.xml', sitemap, {'sitemaps': sitemaps_dict}, name='django.contrib.sitemaps.views.sitemap'),
	path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain; charset=utf-8')),
	path('llms.txt', TemplateView.as_view(template_name='llms.txt', content_type='text/plain; charset=utf-8')),
	path('llms-full.txt', TemplateView.as_view(template_name='llms-full.txt', content_type='text/plain; charset=utf-8')),
	# path('test404/', TemplateView.as_view(template_name='404.html')),
	# path('test500/', TemplateView.as_view(template_name='500.html')),
	# re_path('admin/', admin.site.urls),
	re_path('^api/captcha/image/$', pomelo_test_utils.common_captcha_img, name='common_captcha_img'),
	re_path('^api/captcha/refresh/$', pomelo_test_utils.common_refresh_captcha, name='common_refresh_captcha'),
	re_path('^$', pomelo_views.index),
	re_path('index/', pomelo_views.index, name="index"),
	re_path('^A000_news/$', pomelo_views.new_news),
	re_path('^A000_news/page/(?P<page>\d+)/$', pomelo_views.new_news),
	re_path('A000_news/(?P<slug>[\w\d]+)/', pomelo_views.new_news_detail, name='news_detail'),
	re_path('^A000_reports/$', pomelo_views.new_medias),
	re_path('^A000_reports/page/(?P<page>\d+)/$', pomelo_views.new_medias),
	re_path('A000_reports/(?P<slug>[\w\d_-]+)/', pomelo_views.new_media_detail, name='media_detail'),
	re_path('A000_closed_clinic/', pomelo_views.new_stop_show),
	re_path('A000_video_message/', pomelo_views.new_video),
	re_path('^A000_medical_info/$', pomelo_views.medical_info), # 醫療資訊 (清單頁)
	re_path('^A000_medical_info/page/(?P<page>\d+)/$', pomelo_views.medical_info), # 醫療資訊 (AJAX 分頁)
	re_path('^A000_medical_info/(?P<slug>[\w\d_-]+)/$', pomelo_views.medical_pages_detail, name='medical_detail'), # 醫療資訊(詳細頁-短網址)
	re_path('A000_medical_pages/', pomelo_views.medical_pages),
	re_path('^A001_department_overview/$', pomelo_views.A001_department_overview),
	re_path('^A001_department_overview/(?P<dept_en>[\w\d_-]+)/$', pomelo_views.A001_department_part_short),
	re_path('^A001_department_part/$', pomelo_views.A001_department_part),
	re_path('^A001_department_doctor/$', pomelo_views.A001_department_doctor),
	re_path('^A001_department_doctor/(?P<dept_en>[\w\d_-]+)/(?P<dr_id>[\w\d_-]+)/$', pomelo_views.A001_department_doctor_short),
	re_path('^A001_dr_search/$', pomelo_views.A001_dr_search),
	re_path('A002_consultation_progress/', pomelo_views.A002_consultation_progress),
	re_path('A002_registration_notice/', pomelo_views.A002_registration_notice),
	re_path('A002_which_disease/', pomelo_views.A002_which_disease),
	re_path('A002_clinic_time/', pomelo_views.A002_clinic_time),
	re_path('A002_payment_machine/', pomelo_views.A002_payment_machine), # 未開放
	re_path('A002_self_service/', pomelo_views.A002_self_service),
	re_path('A002_data_apply/', pomelo_views.A002_data_apply),
	re_path('A003_Medical_Support/', pomelo_views.A003_Medical_Support),
	re_path('A003_ER/', pomelo_views.A003_ER),
	re_path('A003_ER_1/', pomelo_views.A003_ER_1),
	re_path('A003_ER_2/', pomelo_views.A003_ER_2),
	re_path('A003_AED/', pomelo_views.A003_AED),
	re_path('A003_AED_1/', pomelo_views.A003_AED_1),
	re_path('A003_Story_1/', pomelo_views.A003_Story_1),
	re_path('A003_Story_2/', pomelo_views.A003_Story_2),
	re_path('A003_Laboratory/', pomelo_views.A003_Laboratory),
	re_path('A003_Laboratory_1/', pomelo_views.A003_Laboratory_1),
	re_path('A003_Laboratory_2/', pomelo_views.A003_Laboratory_2),
	# re_path('A003_Laboratory_3/', pomelo_views.A003_Laboratory_3), # 未開放-抱怨程序
	re_path('A003_Laboratory_4/', pomelo_views.A003_Laboratory_4),
	re_path('A003_labor_blood/', pomelo_views.A003_labor_blood),
	re_path('A003_labor_blood_2/', pomelo_views.A003_labor_blood_2),
	re_path('A003_labor_blood_3/', pomelo_views.A003_labor_blood_3),
	re_path('A003_labor_clinical/', pomelo_views.A003_labor_clinical),
	re_path('A003_labor_clinical_1/', pomelo_views.A003_labor_clinical_1),
	re_path('A003_labor_clinical_2/', pomelo_views.A003_labor_clinical_2),
	re_path('A003_labor_clinical_3/', pomelo_views.A003_labor_clinical_3),
	re_path('A003_labor_clinical_3_3c/', pomelo_views.A003_labor_clinical_3_3c),
	re_path('A003_labor_clinical_3_art/', pomelo_views.A003_labor_clinical_3_art),
	re_path('A003_labor_clinical_3_baby/', pomelo_views.A003_labor_clinical_3_baby),
	re_path('A003_labor_clinical_3_blood/', pomelo_views.A003_labor_clinical_3_blood),
	re_path('A003_labor_clinical_3_cav/', pomelo_views.A003_labor_clinical_3_cav),
	re_path('A003_labor_clinical_3_csf/', pomelo_views.A003_labor_clinical_3_csf),
	re_path('A003_labor_clinical_3_dung/', pomelo_views.A003_labor_clinical_3_dung),
	re_path('A003_labor_clinical_3_ra/', pomelo_views.A003_labor_clinical_3_ra),
	re_path('A003_labor_clinical_3_phlegm/', pomelo_views.A003_labor_clinical_3_phlegm),
	re_path('A003_labor_clinical_3_prepare/', pomelo_views.A003_labor_clinical_3_prepare),
	re_path('A003_labor_clinical_3_respiratory/', pomelo_views.A003_labor_clinical_3_respiratory),
	re_path('A003_labor_clinical_3_semen/', pomelo_views.A003_labor_clinical_3_semen),
	re_path('A003_labor_clinical_3_solid/', pomelo_views.A003_labor_clinical_3_solid),
	re_path('A003_labor_clinical_3_sugar/', pomelo_views.A003_labor_clinical_3_sugar),
	re_path('A003_labor_clinical_3_tract/', pomelo_views.A003_labor_clinical_3_tract),
	re_path('A003_labor_clinical_3_urine/', pomelo_views.A003_labor_clinical_3_urine),
	re_path('A003_labor_clinical_3_vein/', pomelo_views.A003_labor_clinical_3_vein),
	re_path('A003_labor_clinical_3_wine/', pomelo_views.A003_labor_clinical_3_wine),
	re_path('A003_labor_clinical_4/', pomelo_views.A003_labor_clinical_4),
	re_path('A003_labor_clinical_4_abscess/', pomelo_views.A003_labor_clinical_4_abscess),
	re_path('A003_labor_clinical_4_bf/', pomelo_views.A003_labor_clinical_4_bf),
	re_path('A003_labor_clinical_4_bottle/', pomelo_views.A003_labor_clinical_4_bottle),
	re_path('A003_labor_clinical_4_collection/', pomelo_views.A003_labor_clinical_4_collection),
	re_path('A003_labor_clinical_4_dung/', pomelo_views.A003_labor_clinical_4_dung),
	re_path('A003_labor_clinical_4_eye/', pomelo_views.A003_labor_clinical_4_eye),
	re_path('A003_labor_clinical_4_respiratory/', pomelo_views.A003_labor_clinical_4_respiratory),
	re_path('A003_labor_clinical_4_urine/', pomelo_views.A003_labor_clinical_4_urine),
	re_path('A003_labor_clinical_5/', pomelo_views.A003_labor_clinical_5),
	re_path('A003_labor_clinical_6/', pomelo_views.A003_labor_clinical_6), # 檢驗服務項目 (asp)
	re_path('A003_labor_clinical_7/', pomelo_views.A003_labor_clinical_7),
	re_path('A003_labor_clinical_8/', pomelo_views.A003_labor_clinical_8),
	re_path('A003_labor_clinical_9/', pomelo_views.A003_labor_clinical_9), # 報告單位換算 (asp)
	re_path('A003_labor_clinical_in_b/', pomelo_views.A003_labor_clinical_in_b),
	re_path('A003_labor_clinical_in_du/', pomelo_views.A003_labor_clinical_in_du),
	re_path('A003_labor_clinical_in_glu/', pomelo_views.A003_labor_clinical_in_glu),
	re_path('A003_labor_clinical_in_ig/', pomelo_views.A003_labor_clinical_in_ig),
	re_path('A003_labor_clinical_in_occ/', pomelo_views.A003_labor_clinical_in_occ),
	re_path('A003_labor_clinical_in_pin/', pomelo_views.A003_labor_clinical_in_pin),
	re_path('A003_labor_clinical_in_sem/', pomelo_views.A003_labor_clinical_in_sem),
	re_path('A003_labor_clinical_in_spu/', pomelo_views.A003_labor_clinical_in_spu),
	re_path('A003_labor_clinical_in_third/', pomelo_views.A003_labor_clinical_in_third),
	re_path('A003_labor_clinical_in_urine/', pomelo_views.A003_labor_clinical_in_urine),
	re_path('A003_labor_Genetic/', pomelo_views.A003_labor_Genetic),
	re_path('A003_labor_Genetic_1/', pomelo_views.A003_labor_Genetic_1),
	re_path('A003_labor_pathology/', pomelo_views.A003_labor_pathology),
	re_path('A003_labor_pathology_1/', pomelo_views.A003_labor_pathology_1),
	re_path('A003_labor_pathology_2/', pomelo_views.A003_labor_pathology_2),
	re_path('A003_labor_pathology_3/', pomelo_views.A003_labor_pathology_3),
	re_path('A003_labor_pathology_4/', pomelo_views.A003_labor_pathology_4),
	re_path('A003_labor_pathology_5/', pomelo_views.A003_labor_pathology_5),
	re_path(r'^A003_health_edu/',include('health_edu.urls')),
	# re_path('A004_hos_intro_test/', pomelo_views.A004_hos_intro_test),
	re_path('A004_hos_intro/', pomelo_views.A004_hos_intro),
	re_path('A004_hos_traffic_info/', pomelo_views.A004_hos_traffic_info),
	re_path('A004_hos_lost_info/', pomelo_views.A004_hos_lost_info),
	re_path('A004_contact_us/', pomelo_views.A004_contact_us),
	re_path('A005_ward_mes_1/', pomelo_views.A005_ward_mes_1),
	# re_path('A005_ward_mes_2/', pomelo_views.A005_ward_mes_2),
	re_path('A005_ward_mes_3/', pomelo_views.A005_ward_mes_3),
	re_path('A005_ward_mes_4/', pomelo_views.A005_ward_mes_4),
	re_path('A005_ward_mes_0/', pomelo_views.A005_ward_mes_0),
	# re_path('A005_Diff_fee/', pomelo_views.A005_Diff_fee),
	re_path('A005_Self_fee/', pomelo_views.A005_Self_fee),
	re_path('A006_Online_Booking_0/', pomelo_views.A006_Online_Booking_0),
	# re_path('A006_Online_Booking_0/<url>/', pomelo_views.A006_Online_Booking_0),
	re_path('A006_Online_Booking_0_0/', pomelo_views.A006_Online_Booking_0_0),
	re_path('A006_Online_Booking_login/', pomelo_views.A006_Online_Booking_login),
	re_path('A006_Online_Booking_first/', pomelo_views.A006_Online_Booking_first), # 初診資料填寫
	re_path('A006_Online_Booking_data/', pomelo_views.A006_Online_Booking_data), # 預約資料記錄
	re_path('A006_Online_Booking_check/', pomelo_views.A006_Online_Booking_check),
	re_path('A006_Online_Booking_1/', pomelo_views.A006_Online_Booking_1),
	re_path('^A006_Online_Booking_1_part/$', pomelo_views.A006_Online_Booking_1_part_legacy), # 科別預約頁(舊網址轉接)
	re_path('^A006_Online_Booking_1_part/(?P<dept_en>[\w\d_-]+)/$', pomelo_views.A006_Online_Booking_1_part_short), # 科別預約頁(新網址)
	re_path('A006_Online_Booking_2/', pomelo_views.A006_Online_Booking_2),
	re_path('^A006_Online_Booking_2_1/$', pomelo_views.A006_Online_Booking_2_1_legacy), # 醫師預約頁(舊網址轉接)
	re_path('^A006_Online_Booking_2_1/(?P<dept_en>[\w\d_-]+)/(?P<dr_id>[\w\d_-]+)/$', pomelo_views.A006_Online_Booking_2_1_short), # 醫師預約頁(新網址)
	re_path('A006_sign_out/', pomelo_views.A006_sign_out),
	re_path('A006_register/', pomelo_views.A006_register),
	re_path('A006_find_register/', pomelo_views.A006_find_register),
	re_path('A006_out_register/', pomelo_views.A006_out_register),
	re_path(r'^A007_Reserve_pre/',include('Reserve_Pre.urls')), # 預約慢箋
	re_path('A100_search_sename/', pomelo_views.A100_search_sename),
	re_path('A101_search_bed/', pomelo_views.A101_search_bed),
	re_path('A102_Safe_ISMS/', pomelo_views.A102_Safe_ISMS),
	re_path('A103_search_ITH_bed/', pomelo_views.A103_search_ITH_bed),
	# re_path(r'^web_speech/',include('web_speech.urls')),
	re_path('EECP/', include('EECP.urls')),
	re_path('specialty_medical/', include('specialty_medical.urls')), # 特色醫療-骨科微創手術中心
	re_path('specialty_health/', include('specialty_health.urls')), # 特色醫療-健康管理中心
	re_path('breast-care-center/', include('Breast_Care_Center.urls')), # 特色醫療-乳房中心
	re_path('neuro-center/', include('Neurology_Center.urls')), # 特色醫療-神經醫學中心
	re_path('cardio-center/', include('cardio_center.urls')), # 特色醫療-心血管中心
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 新增 media (讓檔案可下載 - 強制在 DEBUG=False 時也能由 Django 提供)
from django.views.static import serve

# 將對 favicon.ico 的請求永久導向靜態資料夾中的圖示檔案位置
# 同時設定 ^media/ 路由讓伺服器能夠讀取並顯示存放在 settings.MEDIA_ROOT 中的使用者上傳媒體檔案。
urlpatterns += [
	re_path('favicon.ico', RedirectView.as_view(url='/static/common/img/favicon.ico', permanent=True)),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
# handler404 = "Pomelo_API.views.error_404"
# handler500 = "Pomelo_API.views.error_500"
