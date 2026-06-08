from django.db import models
from django.conf import settings
import uuid


class Reel(models.Model):
    RATIO_CHOICES = [
        ('9:16', '9:16 — Vertical (default)'),
        ('1:1',  '1:1 — Square'),
        ('4:5',  '4:5 — Portrait'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reels')
    video       = models.FileField(upload_to='reels/videos/')
    thumbnail   = models.ImageField(upload_to='reels/thumbs/', blank=True, null=True)
    caption     = models.TextField(max_length=2200, blank=True)
    audio_name  = models.CharField(max_length=200, blank=True)
    ratio       = models.CharField(max_length=4, choices=RATIO_CHOICES, default='9:16')
    views       = models.PositiveBigIntegerField(default=0)
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

    def format_views(self):
        v = self.views
        if v >= 1_000_000:
            return f'{v/1_000_000:.1f}M'
        if v >= 1_000:
            return f'{v/1_000:.1f}K'
        return str(v)


class ReelLike(models.Model):
    reel       = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='reel_likes')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_reels')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'reel_likes'
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
        db_table        = 'reel_saves'
        unique_together = ('reel', 'user')


class ReelRepost(models.Model):
    reel       = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='reposts')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reposted_reels')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'reel_reposts'
        unique_together = ('reel', 'user')