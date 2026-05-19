from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q
from .models import Post, PostImage, Like, Save, Comment
from .forms import PostCreateForm, CommentForm


@login_required
def create_post_view(request):
    if request.method == 'POST':
        form = PostCreateForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            images = request.FILES.getlist('images')
            for idx, img in enumerate(images):
                PostImage.objects.create(post=post, image=img, order=idx)

            return redirect('posts:detail', pk=post.pk)
    else:
        form = PostCreateForm()
    return render(request, 'posts/create.html', {'form': form})


def post_detail_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.filter(parent=None).select_related('author').prefetch_related('replies__author')
    comment_form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'is_liked': post.is_liked_by(request.user),
        'is_saved': post.is_saved_by(request.user),
        'images': post.images.all(),
    }
    return render(request, 'posts/detail.html', context)


@login_required
@require_POST
def like_toggle_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like = Like.objects.filter(post=post, user=request.user).first()
    if like:
        like.delete()
        liked = False
    else:
        Like.objects.create(post=post, user=request.user)
        liked = True
    return JsonResponse({'liked': liked, 'count': post.get_likes_count()})


@login_required
@require_POST
def save_toggle_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    save = Save.objects.filter(post=post, user=request.user).first()
    if save:
        save.delete()
        saved = False
    else:
        Save.objects.create(post=post, user=request.user)
        saved = True
    return JsonResponse({'saved': saved})


@login_required
@require_POST
def add_comment_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user

        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                comment.parent = Comment.objects.get(id=parent_id, post=post)
            except Comment.DoesNotExist:
                pass

        comment.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'id': str(comment.id),
                'body': comment.body,
                'author': comment.author.username,
                'avatar': comment.author.avatar.url if comment.author.avatar else None,
                'created_at': comment.created_at.strftime('%b %d'),
                'is_reply': comment.parent_id is not None,
            })

    return redirect('posts:detail', pk=pk)


@login_required
@require_POST
def delete_post_view(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    post.delete()
    return redirect('users:profile', username=request.user.username)


@login_required
def saved_posts_view(request):
    posts = Post.objects.filter(saves__user=request.user).select_related('author').prefetch_related('images')
    return render(request, 'posts/saved.html', {'posts': posts})