from django.urls import path
from . import views
urlpatterns = [
    path('',views.index,name="index"),
    # path('sub-<str:main_item>-<str:sub_item>',views.index2,name="sub_page"),
    # path('search',views.search_page,name="search"),


    # path('Health_Edu_1.html',views.health_1),
    # path('Health_Edu_menu.html',views.Health_Edu_menu),
    # path('bread_pencil.html',views.bread_pencil),
    # -<str:search_text>

    # path("Health_Edu/<str:main_item>/<str:sub_item>",views.healthEdu_detail,name="detail"),
    # path("<int:question_id>/test",views.test, name="test")
    # path('',views.),

    
]