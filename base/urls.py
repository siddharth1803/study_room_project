from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('login/', views.login_page, name="login"),
    path('register/', views.register_page, name="register"),
    path('update_user/', views.update_user, name="update_user"),
    path('logout/', views.log_out, name="logout"),
    path('user_profile/<str:key>/', views.user_profile, name="user_profile"),
    path('room/<str:key>/', views.room, name="room"),
    path('create_room/', views.create_room, name="create_room"),
    path('update_room/<str:key>/', views.update_room, name="update_room"),
    path('delete_room/<str:key>/', views.delete_room, name="delete_room"),
    path('delete_message/<str:key>/', views.delete_message, name="delete_message"),
    path('update_message/<str:key>/', views.update_message, name="update_message"),
    path('topics_page/', views.topics_page, name="topics_page"),
    path('activities_page/', views.activities_page, name="activities_page"),
]
