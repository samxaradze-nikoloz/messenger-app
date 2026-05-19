from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
import uuid


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    website = models.URLField(blank=True)
    is_private = models.BooleanField(default=False)
    followers = models.ManyToManyField(
        'self',
        through='Follow',
        symmetrical=False,
        related_name='following_set'
    )

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username

    def get_followers_count(self):
        return Follow.objects.filter(following=self, accepted=True).count()

    def get_following_count(self):
        return Follow.objects.filter(follower=self, accepted=True).count()

    def get_posts_count(self):
        return self.posts.count()

    def is_followed_by(self, user):
        return Follow.objects.filter(follower=user, following=self, accepted=True).exists()

    def has_pending_request(self, user):
        return Follow.objects.filter(follower=user, following=self, accepted=False).exists()


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_rel')
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=True)  # False if account is private

    class Meta:
        unique_together = ('follower', 'following')
        db_table = 'follows'

    def __str__(self):
        return f"{self.follower} → {self.following}"