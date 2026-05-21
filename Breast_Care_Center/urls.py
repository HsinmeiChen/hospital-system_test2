"""Breast Care Center URL Configuration"""
from django.urls import path
from . import views

urlpatterns = [
    # ═════════════ 首頁 ═════════════
    path('', view=views.breast_main, name="breast_home"),
    path('api/banner-data/', views.breast_banner_api, name='breast_banner_api'),
    path('api/breast-news-home/', views.breast_news_home_api, name='breast_news_home_api'),
    path('api/breast-film-home/', views.breast_film_home_api, name='breast_film_home_api'),
    path('api/breast-media-home/', views.breast_media_home_api, name='breast_media_home_api'),

    # ═════════════ 關於我們 ═════════════
    path('breast-about/', view=views.breast_about, name="breast_about"),

    # ═════════════ 最新消息 ═════════════
    path('breast-news/', view=views.breast_news_list_view, name='breast_news'),
    path("api/breast-news/", views.breast_news_api, name="breast_news_api"),
    path('breast-news/<str:key>/', view=views.breast_news_detail_view, name='breast_news_detail'),

    # ═════════════ 媒體報導 ═════════════
    path('breast-media/', view=views.breast_media, name='breast_media'),
    path('api/breast-media/', views.breast_media_api, name='breast_media_api'),
    path('api/random-breast-reports/', views.random_breast_reports_api, name='random_breast_reports_api'),
    path('articles/<str:get_filename>/', views.article_share_view, name='article_share_view'),

    # ═════════════ 影音專區 ═════════════
    path('breast-film/', views.breast_film, name='breast_film'),
    path('api/breast-film-api/', views.breast_film_api, name='breast_film_api'),

    # ═════════════ 醫師陣容 ═════════════
    path('breast-doctor/', views.doctor_list, name='breast_doctor_list'),
    path('api/stop-info/<str:employee_id>/', views.api_stop_info, name='api_stop_info'),

    path('doctor/<str:employee_id>/', views.doctor_profile, name='breast_doctor_profile'),
    path('api/doctor_sidenav/', views.doctor_sidenav_api, name='breast_doctor_sidenav_api'),
    path('api/doctor/<str:employee_id>/articles/', views.get_related_articles_api, name='breast_api_related_articles'),
    path('video-section/<str:employee_id>/', views.video_section_ajax, name='breast_video_section_ajax'),

    # ═════════════ 治療項目 ═════════════
    path('breast-treatment/', views.treatment_list, name='breast_treatment_list'),
    path('breast-treatment/<str:url_name>/', views.treatment_article, name='breast_treatment_article'),
    path('api/breast-treatment/sidenav/', views.treatment_sidenav_api, name='breast_treatment_sidenav_api'),

    # ═════════════ 衛教園地 ═════════════
    path('breast-edu/', views.breast_edu, name='breast_edu'),
    path('api/breast-edu/', views.breast_edu_api, name='breast_edu_api'),
    path('breast-edu/<str:title_id>/', views.breast_edu_detail, name='breast_edu_detail'),
    path('api/random-breast-edus/', views.random_breast_edus_api, name='random_breast_edus_api'),

    # ═════════════ 聯絡我們 ═════════════
    path('contact/', views.breast_send_mail, name='breast_send_mail'),
]
