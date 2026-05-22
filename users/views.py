from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from feed.views import feed_view as feed_app_view
from .models import User, Follow
from .forms import RegisterForm, LoginForm, ProfileEditForm


def home_view(request):
    if request.user.is_authenticated:
        return redirect('users:feed')
    return redirect('users:login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('users:feed')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome! Your account has been created.')
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
            return redirect(next_url if next_url else 'users:profile', username=user.username) \
                if not next_url else redirect(next_url)
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
    is_following = False
    has_pending = False

    if request.user.is_authenticated and not is_own_profile:
        is_following = profile_user.is_followed_by(request.user)
        has_pending = profile_user.has_pending_request(request.user)

    # Determine if posts are visible
    show_posts = is_own_profile or not profile_user.is_private or is_following
    posts = profile_user.posts.all().order_by('-created_at') if show_posts else []

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'is_following': is_following,
        'has_pending': has_pending,
        'posts': posts,
        'show_posts': show_posts,
        'followers_count': profile_user.get_followers_count(),
        'following_count': profile_user.get_following_count(),
        'posts_count': profile_user.get_posts_count(),
    }
    return render(request, 'users/profile.html', context)


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
        action = 'requested' if target.is_private else 'followed'

    return JsonResponse({
        'action': action,
        'followers_count': target.get_followers_count(),
    })


@login_required
def followers_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    followers = list(User.objects.filter(
        following__following=profile_user,
        following__accepted=True
    ))

    followed_ids = set(
        Follow.objects.filter(follower=request.user, accepted=True)
        .values_list('following_id', flat=True)
    )
    for user in followers:
        user.is_followed = user.id in followed_ids

    return render(request, 'users/followers.html', {
        'profile_user': profile_user,
        'users_list': followers,
        'list_type': 'Followers',
    })


@login_required
def following_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    following = list(User.objects.filter(
        followers_rel__follower=profile_user,
        followers_rel__accepted=True
    ))

    followed_ids = set(
        Follow.objects.filter(follower=request.user, accepted=True)
        .values_list('following_id', flat=True)
    )
    for user in following:
        user.is_followed = user.id in followed_ids

    return render(request, 'users/followers.html', {
        'profile_user': profile_user,
        'users_list': following,
        'list_type': 'Following',
    })


def search_view(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        results = User.objects.filter(username__icontains=q) | \
                  User.objects.filter(first_name__icontains=q) | \
                  User.objects.filter(last_name__icontains=q)
        results = results.distinct()
    return render(request, 'users/search.html', {'results': results, 'query': q})


@login_required
def feed_view(request):
    return feed_app_view(request)


@login_required
def my_posts_view(request):
    posts = request.user.posts.all().prefetch_related('images')
    return render(request, 'users/my_posts.html', {'posts': posts})
