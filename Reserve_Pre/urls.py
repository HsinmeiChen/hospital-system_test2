from django.urls import re_path,path
from Reserve_Pre import views

urlpatterns = [
    re_path('login/', views.A007_Reserve_pre_login),
    re_path('reserve/', views.A007_Reserve_pre_reserve),
    re_path('logout/', views.A007_Reserve_pre_logout),
    re_path('data/', views.A007_Reserve_pre_data),
]