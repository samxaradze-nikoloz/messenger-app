from django.urls import path
from . import views
 
app_name = 'users'
 
urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('feed/', views.feed_view, name='feed'),
    path('search/', views.search_view, name='search'),
    path('edit/', views.edit_profile_view, name='edit_profile'),
    path('me/', views.my_posts_view, name='my_posts'),
    path('<str:username>/follow/', views.follow_toggle_view, name='follow_toggle'),
    path('<str:username>/followers/', views.followers_view, name='followers'),
    path('<str:username>/following/', views.following_view, name='following'),
    path('<str:username>/', views.profile_view, name='profile'),
]
 
