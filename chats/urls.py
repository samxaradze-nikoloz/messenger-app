from django.urls import path
from . import views

app_name = 'chats'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('list/', views.home_view, name='list'),
    path('start/<str:username>/', views.start_dm_view, name='start_dm'),
    path('friend-request/<str:username>/', views.friend_request_view, name='friend_request'),
]
