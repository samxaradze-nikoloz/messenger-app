from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('',                        views.notifications_view,  name='list'),
    path('unread/',                 views.unread_count_view,   name='unread'),
    path('<uuid:notif_id>/read/',   views.mark_read_view,      name='mark_read'),
    path('clear/',                  views.clear_all_view,      name='clear'),
]