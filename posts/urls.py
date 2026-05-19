from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('create/', views.create_post_view, name='create'),
    path('saved/', views.saved_posts_view, name='saved'),
    path('<uuid:pk>/', views.post_detail_view, name='detail'),
    path('<uuid:pk>/like/', views.like_toggle_view, name='like'),
    path('<uuid:pk>/save/', views.save_toggle_view, name='save'),
    path('<uuid:pk>/comment/', views.add_comment_view, name='comment'),
    path('<uuid:pk>/delete/', views.delete_post_view, name='delete'),
]