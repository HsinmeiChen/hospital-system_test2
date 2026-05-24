from django.urls import path
from . import views

urlpatterns = [
	path('', views.index, name="index"),
	path('search/', views.search_page, name="search"),
	path('<str:sub_item_en>/', views.index2, name="sub_page"),
	path('<str:sub_item_en>/<str:title_name>/', views.detail_page, name="detail_page"),
]