""" URL Configuration"""
from django.urls import path
from . import views

# 宣告命名空間 (Namespace)，這個名稱通常跟您的 app 名稱一樣
app_name = 'cardio_center'

urlpatterns = [
	# ═════════════ 首頁 ═════════════
	path('', view=views.cardio_main, name="home"),
	path('api/banner-data/', views.cardio_banner_api, name="banner-api"),
	path('api/news-home/', views.cardio_news_home_api, name="news-home-api"),
	path('api/film-home/', views.cardio_film_home_api, name="film-home-api"),
	path('api/media-home/', views.cardio_media_home_api, name="media-home-api"),

	# ═════════════ 關於我們 ═════════════
	path('about/', view=views.cardio_about, name="about"),

	# ═════════════ 最新消息 ═════════════
	path('news/', view=views.cardio_news_list_view, name="news"),
	path('api/news/', views.cardio_news_api, name="news-api"),
	path('news/<str:key>/', view=views.cardio_news_detail_view, name="news-detail"),

	# ═════════════ 媒體報導 ═════════════
	path('media/', view=views.cardio_media, name="media"),
	path('api/media/', views.cardio_media_api, name="media-api"),
	path('api/random-reports/', views.random_cardio_reports_api, name="random-reports-api"),
	path('articles/<str:get_filename>/', views.article_share_view, name="article_share_view"),

	# ═════════════ 影音專區 ═════════════
	path('film/', views.cardio_film, name="film"),
	path('api/film-api/', views.cardio_film_api, name="film-api"),
	path('film/<str:video_key>/', views.cardio_film_detail, name="film-detail"),

	# ═════════════ 醫師陣容 ═════════════
	path('doctor/', views.doctor_list, name="doctor-list"),
	path('api/stop-info/<str:employee_id>/', views.api_stop_info, name="api-stop-info"),

	path('doctor/<str:employee_id>/', views.doctor_profile, name="doctor-profile"),
	path('api/doctor_sidenav/', views.doctor_sidenav_api, name="doctor-sidenav-api"),
	path('api/doctor/<str:employee_id>/articles/', views.get_related_articles_api, name="api-related-articles"),
	path('video-section/<str:employee_id>/', views.video_section_ajax, name="video-section-ajax"),

	# ═════════════ 治療項目 ═════════════
	path('treatment/', views.treatment_list, name="treatment-list"),
	path('treatment/<str:url_name>/', views.treatment_article, name="treatment-article"),
	path('api/treatment/sidenav/', views.treatment_sidenav_api, name="treatment-sidenav-api"),

	# ═════════════ 衛教園地 ═════════════
	path('edu/', views.cardio_edu, name="edu"),
	path('api/edu/', views.cardio_edu_api, name="edu-api"),
	path('edu/<str:title_id>/', views.cardio_edu_detail, name="edu-detail"),
	path('api/random-edus/', views.random_cardio_edus_api, name="random-edus-api"),

	# ═════════════ 聯絡我們 ═════════════
	path('contact/', views.cardio_send_mail, name="send-mail"),
]

