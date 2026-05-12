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
from django.urls import path, include
from . import views

urlpatterns = [
    # path('hello/', view=views.hello_world),
    path('', view=views.health_main, name="health_home"), # 前台-首頁
    path('api/banner-data/', views.health_banner_api, name='health_banner_api'), # 首頁-Banner
    path('api/health-news-home/', views.health_news_home_api, name='health_news_home_api'), # 首頁-最新消息
    path('api/health-film-home/', views.health_film_home_api, name='health_film_home_api'), # 首頁-影音專區
    path('api/health-media-home/', views.health_media_home_api, name='health_media_home_api'), # 首頁-媒體報導
    # path('api/contact/', views.contact_form_view, name='contact_form'), # 首頁-聯繫我們
    path('health-about/', view=views.health_about, name='health_about'),

    path('health-news/', view=views.health_news_list_view, name='health_news'), # 最新消息列表-主頁
    path("api/health-news/", views.health_news_api, name="health_news_api"), # 最新消息-列表分頁(AJAX)
    path('health-news/<str:key>/', view=views.health_news_detail_view, name='health_news_detail'), # 最新消息-文章頁

    path('health-media/', view=views.health_media, name='health_media'), # 媒體報導列表-主頁
    path('api/health-media/', views.health_media_api, name='health_media_api'), # 媒體報導-列表分頁(Ajax) 
    path('api/random_health_reports/', views.random_health_reports_api, name='random_health_reports_api'), # 媒體報導文章頁-隨機取 5 筆文章（供 article_detail 側欄卡片用
    path('articles/<str:get_filename>/', views.article_share_view, name='article_share_view'),

    path('health-health-film/', views.health_film, name='health_film'), # 「影音專區」 主頁
    path('api/health-film-api/', views.health_film_api, name='health_film_api'), # 「影音專區」- 前端用 Ajax 呼叫，動態載入影片文章。

    path('health-health-edu/', view=views.health_health_edu),  # 衛教園地列表-主頁
    path('api/health-edu/', views.health_edu_api, name='health_edu_api'),  # 衛教園地 AJAX 分頁 API
    
    path('health-doctor/', views.doctor_list, name='health_doctor_list'), # 醫師陣容列表-主頁
    path('api/stop-info/<str:employee_id>/', views.api_stop_info, name='health_api_stop_info'), # 醫師陣容列表-主頁(停休診時間)
    path('doctor/<str:employee_id>/', views.doctor_profile, name='health_doctor_profile'), # 醫師介紹頁
    path('api/doctor_sidenav/', views.doctor_sidenav_api, name='health_doctor_sidenav_api'), # 醫師介紹頁-側邊選單(AJAX)
    path('articles/<str:get_filename>/', views.article_share_view, name='health_article_share_view'),
    path('api/doctor/<str:employee_id>/articles/', views.get_related_articles_api, name='health_api_related_articles'), # 醫師介紹頁(相關文章)-分頁(AJAX)
    path('video-section/<str:employee_id>/', views.video_section_ajax, name='health_video_section_ajax'), # 醫師介紹頁(影音專區)-分頁(AJAX)

    path('health-treatment/', views.health_treatment_list, name='health_treatment_list'), # 健檢專案列表-主頁
    path('health-treatment/<str:url_name>/', views.health_treatment_article, name='health_treatment_article'), # 健檢專案-文章頁
    path('api/health-treatment/sidenav/', views.health_treatment_sidenav_api, name='health_treatment_sidenav_api'),  # 健檢專案文章頁-側邊選單(AJAX)

    path('view-pdf/<str:download_type>/<str:filename>/', views.view_pdf_file, name='health_view_pdf_file'),  # 安全下載 PDF 檔案

    path('contact/', views.send_mail, name='health_send_mail'), # 聯絡我們-表單頁面
    path('api/refresh-captcha/', views.refresh_captcha, name='health_refresh_captcha'),  # 聯絡我們-AJAX 刷新驗證碼
    path('api/captcha-image/', views.generate_captcha_image, name='health_captcha_image'),  # 聯絡我們-新增驗證碼圖片 API (pillow 產生圖片)
]
