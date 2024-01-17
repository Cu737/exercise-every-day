"""
URL configuration for ExerciseEveryDay project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path
from app01 import views

urlpatterns = [
    # 转入登录界面
    path('login/', views.login, name='login'),
    path('index/home/', views.index_home, name='index_home'),
    path('index/home_fwc/', views.index_home_fwc, name='index_home_fwc'),
    path('index/ranking/', views.index_ranking, name='index_ranking'),
    path('game/', views.game),
    path('signup/', views.signup, name='signup'),
    path('image/code/', views.image_code),
    path('logout/', views.logout),
    path('video/',views.video),
    path('update-score/',views.update_score),
    path('update-fwc-score/',views.update_fwc_score),
    path('fwc/', views.fwc_view),
    path('get_counter_data/', views.get_counter_data, name='get_counter_data'),
   # path('index/ranking/', views.top_three_scores, name='top_three_scores')
]
