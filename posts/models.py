from django.db import models
from django.conf import settings
import uuid


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    caption = models.TextField(max_length=2200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'posts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.username} — {self.created_at:%Y-%m-%d}"

    def get_likes_count(self):
        return self.likes.count()

    def get_comments_count(self):
        return self.comments.filter(parent=None).count()

    def is_liked_by(self, user):
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()

    def is_saved_by(self, user):
        if not user.is_authenticated:
            return False
        return self.saves.filter(user=user).exists()


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='post_uploads/')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'post_images'
        ordering = ['order']


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'likes'
        unique_together = ('post', 'user')


class Save(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saves')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saves'
        unique_together = ('post', 'user')


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comments'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username}: {self.body[:40]}"