""" URL Configuration"""
from django.urls import path
from . import views

urlpatterns = [
	# ═════════════ 首頁 ═════════════
	path('', view=views.neuro_main, name="neuro_home"),
	path('api/banner-data/', views.neuro_banner_api, name='neuro_banner_api'),
	path('api/neuro-news-home/', views.neuro_news_home_api, name='neuro_news_home_api'),
	path('api/neuro-film-home/', views.neuro_film_home_api, name='neuro_film_home_api'),
	path('api/neuro-media-home/', views.neuro_media_home_api, name='neuro_media_home_api'),

	# ═════════════ 關於我們 ═════════════
	path('neuro-about/', view=views.neuro_about, name="neuro_about"),

	# ═════════════ 最新消息 ═════════════
	path('neuro-news/', view=views.neuro_news_list_view, name='neuro_news'),
	path("api/neuro-news/", views.neuro_news_api, name="neuro_news_api"),
	path('neuro-news/<str:key>/', view=views.neuro_news_detail_view, name='neuro_news_detail'),

	# ═════════════ 媒體報導 ═════════════
	path('neuro-media/', view=views.neuro_media, name='neuro_media'),
	path('api/neuro-media/', views.neuro_media_api, name='neuro_media_api'),
	path('api/random-neuro-reports/', views.random_neuro_reports_api, name='random_neuro_reports_api'),
	path('articles/<str:get_filename>/', views.article_share_view, name='article_share_view'),

	# ═════════════ 影音專區 ═════════════
	path('neuro-film/', views.neuro_film, name='neuro_film'),
	path('api/neuro-film-api/', views.neuro_film_api, name='neuro_film_api'),
	path('neuro-film/<str:video_key>/', views.neuro_film_detail, name='neuro_film_detail'),

	# ═════════════ 醫師陣容 ═════════════
	path('neuro-doctor/', views.doctor_list, name='neuro_doctor_list'),
	path('api/stop-info/<str:employee_id>/', views.api_stop_info, name='api_stop_info'),

	path('doctor/<str:employee_id>/', views.doctor_profile, name='neuro_doctor_profile'),
	path('api/doctor_sidenav/', views.doctor_sidenav_api, name='neuro_doctor_sidenav_api'),
	path('api/doctor/<str:employee_id>/articles/', views.get_related_articles_api, name='neuro_api_related_articles'),
	path('video-section/<str:employee_id>/', views.video_section_ajax, name='neuro_video_section_ajax'),

	# ═════════════ 治療項目 ═════════════
	path('neuro-treatment/', views.treatment_list, name='neuro_treatment_list'),
	path('neuro-treatment/<str:url_name>/', views.treatment_article, name='neuro_treatment_article'),
	path('api/neuro-treatment/sidenav/', views.treatment_sidenav_api, name='neuro_treatment_sidenav_api'),

	# ═════════════ 衛教園地 ═════════════
	path('neuro-edu/', views.neuro_edu, name='neuro_edu'),
	path('api/neuro-edu/', views.neuro_edu_api, name='neuro_edu_api'),
	path('neuro-edu/<str:title_id>/', views.neuro_edu_detail, name='neuro_edu_detail'),
	path('api/random-neuro-edus/', views.random_neuro_edus_api, name='random_neuro_edus_api'),

	# ═════════════ 聯絡我們 ═════════════
	path('contact/', views.neuro_send_mail, name='neuro_send_mail'),
]

