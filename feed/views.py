from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Exists, OuterRef
from posts.models import Post, Like, Save
from users.models import Follow


@login_required
def feed_view(request):
    tab = request.GET.get('tab', 'following')

    # IDs of people this user follows
    following_ids = Follow.objects.filter(
        follower=request.user,
        accepted=True
    ).values_list('following_id', flat=True)

    if tab == 'following':
        author_ids = list(following_ids) + [request.user.id]
        posts = Post.objects.filter(
            author_id__in=author_ids
        ).select_related('author').prefetch_related('images', 'likes', 'comments')
    else:
        # "For You" — posts from everyone except self, ordered by likes
        posts = Post.objects.exclude(
            author=request.user
        ).select_related('author').prefetch_related('images', 'likes', 'comments')\
         .annotate(like_count=Count('likes'))\
         .order_by('-like_count', '-created_at')

    # Annotate liked/saved status per post
    liked_ids = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    saved_ids = set(Save.objects.filter(user=request.user).values_list('post_id', flat=True))

    posts_data = []
    for post in posts[:40]:
        posts_data.append({
            'post': post,
            'is_liked': post.id in liked_ids,
            'is_saved': post.id in saved_ids,
            'images': post.images.all(),
        })

    context = {
        'tab': tab,
        'posts_data': posts_data,
        'has_following': bool(following_ids),
    }
    return render(request, 'feed/feed.html', context)