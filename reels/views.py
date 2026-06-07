from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def home_view(request):
    return render(request, 'reels/index.html')
from django.urls import path
from django.shortcuts import render

app_name = 'reels'

def placeholder(request):
    return render(request, 'reels/placeholder.html')

urlpatterns = [
    path('', placeholder, name='list'),
]
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Reel, ReelLike, ReelSave, ReelComment, ReelRepost
from users.models import User


# ── Feed ─────────────────────────────────────────────────────────
@login_required
def reel_feed_view(request):
    reels = Reel.objects.select_related('author').prefetch_related(
        'reel_likes', 'reel_comments'
    ).order_by('-created_at')

    liked_ids = set(ReelLike.objects.filter(user=request.user).values_list('reel_id', flat=True))
    saved_ids = set(ReelSave.objects.filter(user=request.user).values_list('reel_id', flat=True))
    repost_ids = set(ReelRepost.objects.filter(user=request.user).values_list('reel_id', flat=True))

    reels_data = [{
        'reel':      r,
        'is_liked':  r.id in liked_ids,
        'is_saved':  r.id in saved_ids,
        'is_reposted': r.id in repost_ids,
    } for r in reels]

    return render(request, 'reels/feed.html', {'reels_data': reels_data})


# ── Create ────────────────────────────────────────────────────────
@login_required
def create_reel_view(request):
    if request.method == 'POST':
        video     = request.FILES.get('video')
        thumbnail = request.FILES.get('thumbnail')
        caption   = request.POST.get('caption', '').strip()
        audio     = request.POST.get('audio_name', 'Original audio').strip()

        if not video:
            return render(request, 'reels/create.html', {'error': 'Please select a video.'})

        reel = Reel.objects.create(
            author=request.user,
            video=video,
            thumbnail=thumbnail or None,
            caption=caption,
            audio_name=audio or 'Original audio',
        )
        return redirect('reels:feed')

    return render(request, 'reels/create.html')


# ── Detail ────────────────────────────────────────────────────────
def reel_detail_view(request, pk):
    reel     = get_object_or_404(Reel, pk=pk)
    comments = reel.reel_comments.select_related('author').order_by('created_at')

    return render(request, 'reels/detail.html', {
        'reel':       reel,
        'comments':   comments,
        'is_liked':   reel.is_liked_by(request.user),
        'is_saved':   reel.is_saved_by(request.user),
        'is_reposted': ReelRepost.objects.filter(reel=reel, user=request.user).exists()
                       if request.user.is_authenticated else False,
    })


# ── Like ──────────────────────────────────────────────────────────
@login_required
@require_POST
def like_reel_view(request, pk):
    reel = get_object_or_404(Reel, pk=pk)
    obj  = ReelLike.objects.filter(reel=reel, user=request.user).first()
    if obj:
        obj.delete()
        liked = False
    else:
        ReelLike.objects.create(reel=reel, user=request.user)
        liked = True
    return JsonResponse({'liked': liked, 'count': reel.get_likes_count()})


# ── Save ──────────────────────────────────────────────────────────
@login_required
@require_POST
def save_reel_view(request, pk):
    reel = get_object_or_404(Reel, pk=pk)
    obj  = ReelSave.objects.filter(reel=reel, user=request.user).first()
    if obj:
        obj.delete()
        saved = False
    else:
        ReelSave.objects.create(reel=reel, user=request.user)
        saved = True
    return JsonResponse({'saved': saved})


# ── Repost ────────────────────────────────────────────────────────
@login_required
@require_POST
def repost_reel_view(request, pk):
    reel = get_object_or_404(Reel, pk=pk)
    obj  = ReelRepost.objects.filter(reel=reel, user=request.user).first()
    if obj:
        obj.delete()
        reposted = False
    else:
        ReelRepost.objects.create(reel=reel, user=request.user)
        reposted = True
    return JsonResponse({'reposted': reposted})


# ── Comment ───────────────────────────────────────────────────────
@login_required
@require_POST
def comment_reel_view(request, pk):
    reel = get_object_or_404(Reel, pk=pk)
    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'error': 'Empty'}, status=400)
    c = ReelComment.objects.create(reel=reel, author=request.user, body=body)
    return JsonResponse({
        'id':     str(c.id),
        'body':   c.body,
        'author': c.author.username,
        'avatar': c.author.avatar.url if c.author.avatar else None,
        'time':   c.created_at.strftime('%H:%M'),
    })


# ── Delete ────────────────────────────────────────────────────────
@login_required
@require_POST
def delete_reel_view(request, pk):
    reel = get_object_or_404(Reel, pk=pk, author=request.user)
    reel.delete()
    return redirect('users:profile', username=request.user.username)