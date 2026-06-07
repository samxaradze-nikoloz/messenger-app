from django.db import models
from django.conf import settings
import uuid


class Reel(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reels')
    video       = models.FileField(upload_to='reels/videos/')
    thumbnail   = models.ImageField(upload_to='reels/thumbs/', blank=True, null=True)
    caption     = models.TextField(max_length=2200, blank=True)
    audio_name  = models.CharField(max_length=200, blank=True)   # "Original audio"
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reels'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.username} reel {self.id}"

    def get_likes_count(self):
        return self.reel_likes.count()

    def get_comments_count(self):
        return self.reel_comments.count()

    def is_liked_by(self, user):
        if not user.is_authenticated:
            return False
        return self.reel_likes.filter(user=user).exists()

    def is_saved_by(self, user):
        if not user.is_authenticated:
            return False
        return self.reel_saves.filter(user=user).exists()


class ReelLike(models.Model):
    reel       = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='reel_likes')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_reels')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table      = 'reel_likes'
        unique_together = ('reel', 'user')


class ReelComment(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reel       = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='reel_comments')
    author     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reel_comments')
    body       = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reel_comments'
        ordering = ['created_at']


class ReelSave(models.Model):
    reel       = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='reel_saves')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_reels')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table      = 'reel_saves'
        unique_together = ('reel', 'user')


class ReelRepost(models.Model):
    """User reposts a reel to their profile."""
    reel       = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='reposts')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reposted_reels')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table      = 'reel_reposts'
        unique_together = ('reel', 'user')