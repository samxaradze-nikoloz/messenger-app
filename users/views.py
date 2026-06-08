from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import User, Follow
from .forms import RegisterForm, LoginForm, ProfileEditForm
from django.shortcuts import redirect


def _notify(recipient, sender, notif_type, text=''):
    try:
        from notifications.utils import notify
        notify(recipient, sender, notif_type, text=text)
    except Exception:
        pass


def register_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile', username=request.user.username)
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('users:profile', username=user.username)
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile', username=request.user.username)
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', '')
            return redirect(next_url if next_url else 'feed:feed')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('users:login')


def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    is_own_profile = request.user == profile_user
    is_following   = False
    has_pending    = False
    is_friend      = False
    friend_request_state = 'none'

    if request.user.is_authenticated and not is_own_profile:
        is_following = profile_user.is_followed_by(request.user)
        has_pending  = profile_user.has_pending_request(request.user)
        try:
            from chats.models import Friendship, FriendRequest as FR
            is_friend = Friendship.are_friends(request.user, profile_user)
            if is_friend:
                friend_request_state = 'friends'
            else:
                sent = FR.objects.filter(
                    from_user=request.user, to_user=profile_user, status='pending'
                ).exists()
                friend_request_state = 'sent' if sent else 'none'
        except Exception:
            pass

    show_posts = is_own_profile or not profile_user.is_private or is_following
    posts = profile_user.posts.prefetch_related(
        'images', 'likes', 'comments'
    ).order_by('-created_at') if show_posts else []
    
    # Fetch reels
    own_reels = profile_user.reels.order_by('-created_at') if show_posts else []
    
    # Fetch reposted reels
    reposted_reels = []
    if show_posts:
        try:
            from reels.models import ReelRepost
            reposted_reels = ReelRepost.objects.filter(
                user=profile_user
            ).select_related('reel', 'reel__author').order_by('-created_at')
        except Exception:
            pass

    return render(request, 'users/profile.html', {
        'profile_user':         profile_user,
        'is_own_profile':       is_own_profile,
        'is_following':         is_following,
        'has_pending':          has_pending,
        'is_friend':            is_friend,
        'friend_request_state': friend_request_state,
        'posts':                posts,
        'show_posts':           show_posts,
        'own_reels':            own_reels,
        'reposted_reels':       reposted_reels,
        'followers_count':      profile_user.get_followers_count(),
        'following_count':      profile_user.get_following_count(),
        'posts_count':          profile_user.get_posts_count(),
    })


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('users:profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})


@login_required
@require_POST
def follow_toggle_view(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
    follow_obj = Follow.objects.filter(follower=request.user, following=target).first()
    if follow_obj:
        follow_obj.delete()
        action = 'unfollowed'
    else:
        accepted = not target.is_private
        Follow.objects.create(follower=request.user, following=target, accepted=accepted)
        if accepted:
            action = 'followed'
            _notify(target, request.user, 'follow')
        else:
            action = 'requested'
            _notify(target, request.user, 'follow_request')
    return JsonResponse({'action': action, 'followers_count': target.get_followers_count()})


@login_required
def followers_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    followers = User.objects.filter(
        following__following=profile_user,
        following__accepted=True
    ).select_related()
    return render(request, 'users/followers.html', {
        'profile_user': profile_user,
        'users_list':   followers,
        'list_type':    'Followers',
    })


@login_required
def following_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    following = User.objects.filter(
        followers__follower=profile_user,
        followers__accepted=True
    ).select_related()
    return render(request, 'users/followers.html', {
        'profile_user': profile_user,
        'users_list':   following,
        'list_type':    'Following',
    })


def search_view(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        results = (
            User.objects.filter(username__icontains=q) |
            User.objects.filter(first_name__icontains=q) |
            User.objects.filter(last_name__icontains=q)
        ).distinct()
    return render(request, 'users/search.html', {'results': results, 'query': q})


# Small compatibility redirect views referenced from users/urls.py
def home_view(request):
    return redirect('feed:feed')

def feed_view(request):
    return redirect('feed:feed')

@login_required
def my_posts_view(request):
    return redirect('users:profile', username=request.user.username)