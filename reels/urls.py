from django.urls import path
from . import views

app_name = 'reels'

urlpatterns = [
    path('',                    views.reel_feed_view,    name='feed'),
    path('create/',             views.create_reel_view,  name='create'),
    path('<uuid:pk>/',          views.reel_detail_view,  name='detail'),
    path('<uuid:pk>/like/',     views.like_reel_view,    name='like'),
    path('<uuid:pk>/save/',     views.save_reel_view,    name='save'),
    path('<uuid:pk>/repost/',   views.repost_reel_view,  name='repost'),
    path('<uuid:pk>/comment/',  views.comment_reel_view, name='comment'),
    path('<uuid:pk>/delete/',   views.delete_reel_view,  name='delete'),
]