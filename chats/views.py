from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Max
from django.utils import timezone
from .models import FriendRequest, Friendship, Chat, ChatMember, Message, Call
from users.models import User


# ── Friend Requests ───────────────────────────────────────────────

@login_required
@require_POST
def send_friend_request(request, username):
    to_user = get_object_or_404(User, username=username)
    if to_user == request.user:
        return JsonResponse({'error': 'Cannot add yourself'}, status=400)
    if Friendship.are_friends(request.user, to_user):
        return JsonResponse({'status': 'already_friends'})

    obj, created = FriendRequest.objects.get_or_create(
        from_user=request.user, to_user=to_user,
        defaults={'status': 'pending'}
    )
    if not created and obj.status == 'declined':
        obj.status = 'pending'
        obj.save()

    return JsonResponse({'status': 'sent'})


@login_required
@require_POST
def respond_friend_request(request, request_id):
    freq = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    action = request.POST.get('action')  # 'accept' | 'decline'

    if action == 'accept':
        freq.status = 'accepted'
        freq.save()
        # Create friendship (ordered to prevent dupes)
        u1, u2 = sorted([request.user, freq.from_user], key=lambda u: str(u.pk))
        Friendship.objects.get_or_create(user1=u1, user2=u2)
        # Auto-create a DM chat
        _get_or_create_dm(request.user, freq.from_user)
        return JsonResponse({'status': 'accepted'})
    else:
        freq.status = 'declined'
        freq.save()
        return JsonResponse({'status': 'declined'})


@login_required
def friend_requests_view(request):
    received = FriendRequest.objects.filter(
        to_user=request.user, status='pending'
    ).select_related('from_user').order_by('-created_at')

    sent = FriendRequest.objects.filter(
        from_user=request.user, status='pending'
    ).select_related('to_user').order_by('-created_at')

    friends = Friendship.get_friends(request.user)

    return render(request, 'chats/friends.html', {
        'received': received,
        'sent': sent,
        'friends': friends,
    })


def _get_or_create_dm(user1, user2):
    """Return existing DM chat or create one."""
    existing = Chat.objects.filter(
        chat_type='direct',
        members=user1
    ).filter(members=user2).first()
    if existing:
        return existing
    chat = Chat.objects.create(chat_type='direct')
    ChatMember.objects.create(chat=chat, user=user1)
    ChatMember.objects.create(chat=chat, user=user2)
    return chat


# ── Chat List ────────────────────────────────────────────────────

@login_required
def chat_list_view(request):
    chats = Chat.objects.filter(members=request.user).prefetch_related(
        'members', 'messages'
    ).order_by('-created_at')

    chat_data = []
    for chat in chats:
        last = chat.get_last_message()
        chat_data.append({
            'chat': chat,
            'display_name':   chat.get_display_name(request.user),
            'display_avatar': chat.get_display_avatar(request.user),
            'last_message':   last,
            'unread':         chat.unread_count(request.user),
        })

    # Sort by last message time
    chat_data.sort(
        key=lambda x: x['last_message'].created_at if x['last_message'] else x['chat'].created_at,
        reverse=True
    )

    friend_requests_count = FriendRequest.objects.filter(
        to_user=request.user, status='pending'
    ).count()

    return render(request, 'chats/list.html', {
        'chat_data': chat_data,
        'friend_requests_count': friend_requests_count,
    })


# ── Chat Room ────────────────────────────────────────────────────

@login_required
def chat_room_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, members=request.user)
    messages = chat.messages.select_related('sender', 'reply_to__sender').order_by('created_at')

    # Mark as read
    ChatMember.objects.filter(chat=chat, user=request.user).update(last_read=timezone.now())

    other_user = None
    if chat.chat_type == 'direct':
        other_user = chat.members.exclude(pk=request.user.pk).first()

    return render(request, 'chats/room.html', {
        'chat':       chat,
        'messages':   messages,
        'other_user': other_user,
        'members':    chat.members.all(),
        'is_admin':   chat.chatmember_set.filter(user=request.user, role='admin').exists(),
    })


@login_required
@require_POST
def send_message_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, members=request.user)
    body      = request.POST.get('body', '').strip()
    image     = request.FILES.get('image')
    reply_id  = request.POST.get('reply_to')

    msg_type_override = request.POST.get('msg_type','')
    if not body and not image and not msg_type_override:
        return JsonResponse({'error': 'Empty message'}, status=400)

    msg = Message(chat=chat, sender=request.user)
    if msg_type_override == 'sticker':
        msg.msg_type = 'sticker'
        msg.body     = body
    elif image:
        msg.msg_type = 'image'
        msg.image    = image
    else:
        msg.msg_type = 'text'
        msg.body     = body

    if reply_id:
        try:
            msg.reply_to = Message.objects.get(id=reply_id, chat=chat)
        except Message.DoesNotExist:
            pass

    msg.save()

    return JsonResponse({
        'id':         str(msg.id),
        'body':       msg.body,
        'image_url':  msg.image.url if msg.image else None,
        'msg_type':   msg.msg_type,
        'sender':     msg.sender.username,
        'sender_av':  msg.sender.avatar.url if msg.sender.avatar else None,
        'created_at': msg.created_at.strftime('%H:%M'),
        'reply_to':   {
            'sender': msg.reply_to.sender.username if msg.reply_to else None,
            'body':   msg.reply_to.body[:60] if msg.reply_to else None,
        } if msg.reply_to else None,
    })


@login_required
@require_POST
def delete_message_view(request, chat_id, msg_id):
    msg = get_object_or_404(Message, id=msg_id, chat_id=chat_id, sender=request.user)
    msg.is_deleted = True
    msg.body = ''
    msg.save()
    return JsonResponse({'deleted': True})


# ── Start DM ─────────────────────────────────────────────────────

@login_required
def start_dm_view(request, username):
    other = get_object_or_404(User, username=username)
    chat  = _get_or_create_dm(request.user, other)
    return redirect('chats:room', chat_id=chat.id)


# ── Create Group ─────────────────────────────────────────────────

@login_required
def create_group_view(request):
    friends = Friendship.get_friends(request.user)

    if request.method == 'POST':
        name       = request.POST.get('name', '').strip()
        desc       = request.POST.get('description', '').strip()
        avatar     = request.FILES.get('avatar')
        member_ids = request.POST.getlist('members')

        if not name:
            return render(request, 'chats/create_group.html', {
                'friends': friends, 'error': 'Group name is required'
            })

        chat = Chat.objects.create(
            chat_type='group',
            name=name,
            description=desc,
            created_by=request.user,
        )
        if avatar:
            chat.avatar = avatar
            chat.save()

        # Add creator as admin
        ChatMember.objects.create(chat=chat, user=request.user, role='admin')

        # Add selected members
        for uid in member_ids:
            try:
                member = User.objects.get(pk=uid)
                ChatMember.objects.get_or_create(chat=chat, user=member)
            except User.DoesNotExist:
                pass

        # Info message
        Message.objects.create(
            chat=chat,
            msg_type='info',
            body=f'{request.user.username} created the group "{name}"'
        )

        return redirect('chats:room', chat_id=chat.id)

    return render(request, 'chats/create_group.html', {'friends': friends})


# ── Group Management ─────────────────────────────────────────────

@login_required
def group_info_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, chat_type='group', members=request.user)
    is_admin = chat.chatmember_set.filter(user=request.user, role='admin').exists()
    friends = Friendship.get_friends(request.user)
    current_member_ids = list(chat.members.values_list('pk', flat=True))
    addable = [f for f in friends if f.pk not in current_member_ids]

    return render(request, 'chats/group_info.html', {
        'chat':     chat,
        'members':  chat.chatmember_set.select_related('user').all(),
        'is_admin': is_admin,
        'addable':  addable,
    })


@login_required
@require_POST
def add_group_member_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, chat_type='group')
    if not chat.chatmember_set.filter(user=request.user, role='admin').exists():
        return JsonResponse({'error': 'Not admin'}, status=403)
    uid = request.POST.get('user_id')
    try:
        user = User.objects.get(pk=uid)
        ChatMember.objects.get_or_create(chat=chat, user=user)
        Message.objects.create(chat=chat, msg_type='info',
                                body=f'{request.user.username} added {user.username}')
        return JsonResponse({'status': 'added', 'username': user.username})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@login_required
@require_POST
def remove_group_member_view(request, chat_id, user_id):
    chat = get_object_or_404(Chat, id=chat_id, chat_type='group')
    is_admin = chat.chatmember_set.filter(user=request.user, role='admin').exists()
    is_self  = str(request.user.pk) == str(user_id)
    if not is_admin and not is_self:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    ChatMember.objects.filter(chat=chat, user_id=user_id).delete()
    return JsonResponse({'status': 'removed'})


# ── Calls ────────────────────────────────────────────────────────

@login_required
def call_view(request, chat_id):
    chat      = get_object_or_404(Chat, id=chat_id, members=request.user)
    call_type = request.GET.get('type', 'audio')  # 'audio' | 'video'

    call = Call.objects.create(
        chat=chat, caller=request.user, call_type=call_type
    )
    Message.objects.create(
        chat=chat, sender=request.user, msg_type='call',
        body=f'{call_type}_call:{call.id}'
    )

    other_user = None
    if chat.chat_type == 'direct':
        other_user = chat.members.exclude(pk=request.user.pk).first()

    return render(request, 'chats/call.html', {
        'chat':       chat,
        'call':       call,
        'call_type':  call_type,
        'other_user': other_user,
    })


@login_required
@require_POST
def end_call_view(request, call_id):
    call = get_object_or_404(Call, id=call_id)
    call.ended_at = timezone.now()
    call.status   = request.POST.get('status', 'answered')
    call.save()
    return JsonResponse({'duration': call.duration_seconds})