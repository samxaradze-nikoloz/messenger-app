from django.urls import path
from . import views

app_name = 'chats'

urlpatterns = [
    # Chat list & room
    path('',                                views.chat_list_view,          name='list'),
    path('<uuid:chat_id>/',                 views.chat_room_view,          name='room'),
    path('<uuid:chat_id>/send/',            views.send_message_view,       name='send'),
    path('<uuid:chat_id>/msg/<uuid:msg_id>/delete/', views.delete_message_view, name='delete_msg'),

    # DM shortcut
    path('dm/<str:username>/',              views.start_dm_view,           name='start_dm'),

    # Groups
    path('group/create/',                   views.create_group_view,       name='create_group'),
    path('group/<uuid:chat_id>/info/',      views.group_info_view,         name='group_info'),
    path('group/<uuid:chat_id>/add/',       views.add_group_member_view,   name='add_member'),
    path('group/<uuid:chat_id>/remove/<uuid:user_id>/', views.remove_group_member_view, name='remove_member'),

    # Friends
    path('friends/',                        views.friend_requests_view,    name='friends'),
    path('friends/request/<str:username>/', views.send_friend_request,     name='friend_request'),
    path('friends/respond/<uuid:request_id>/', views.respond_friend_request, name='friend_respond'),

    # Calls
    path('<uuid:chat_id>/call/',            views.call_view,               name='call'),
    path('call/<uuid:call_id>/end/',        views.end_call_view,           name='end_call'),
]