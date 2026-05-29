from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
import uuid


# ── Friend Request ────────────────────────────────────────────────
class FriendRequest(models.Model):
    STATUS = [
        ('pending',  'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    to_user    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests')
    status     = models.CharField(max_length=10, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table      = 'friend_requests'
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"


class Friendship(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user1      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friendships1')
    user2      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friendships2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table      = 'friendships'
        unique_together = ('user1', 'user2')

    @classmethod
    def are_friends(cls, u1, u2):
        return cls.objects.filter(
            models.Q(user1=u1, user2=u2) | models.Q(user1=u2, user2=u1)
        ).exists()

    @classmethod
    def get_friends(cls, user):
        from django.conf import settings
        User = settings.AUTH_USER_MODEL
        qs = cls.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).select_related('user1', 'user2')
        friends = []
        for f in qs:
            friends.append(f.user2 if f.user1 == user else f.user1)
        return friends


# ── Direct / Group Chat ───────────────────────────────────────────
class Chat(models.Model):
    TYPE = [('direct', 'Direct'), ('group', 'Group')]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_type    = models.CharField(max_length=10, choices=TYPE, default='direct')
    # Group-only fields
    name         = models.CharField(max_length=100, blank=True)
    avatar       = models.ImageField(upload_to='group_avatars/', blank=True, null=True)
    description  = models.TextField(max_length=300, blank=True)
    created_by   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='created_chats')
    members      = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                          through='ChatMember', related_name='chats')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'chats'
        ordering  = ['-created_at']

    def __str__(self):
        return self.name or f"Chat {self.id}"

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def get_display_name(self, for_user):
        if self.chat_type == 'group':
            return self.name
        other = self.members.exclude(pk=for_user.pk).first()
        return other.username if other else 'Unknown'

    def get_display_avatar(self, for_user):
        if self.chat_type == 'group':
            return self.avatar.url if self.avatar else None
        other = self.members.exclude(pk=for_user.pk).first()
        return other.avatar.url if other and other.avatar else None

    def unread_count(self, user):
        membership = self.chatmember_set.filter(user=user).first()
        if not membership:
            return 0
        return self.messages.filter(created_at__gt=membership.last_read).exclude(sender=user).count()


class ChatMember(models.Model):
    ROLE = [('admin', 'Admin'), ('member', 'Member')]

    chat      = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role      = models.CharField(max_length=10, choices=ROLE, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table      = 'chat_members'
        unique_together = ('chat', 'user')


# ── Message ───────────────────────────────────────────────────────
class Message(models.Model):
    TYPE = [
        ('text',  'Text'),
        ('image', 'Image'),
        ('call',  'Call'),
        ('sticker','Sticker'),
        ('info',  'Info'),
    ]
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat       = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='sent_messages', null=True, blank=True)
    msg_type   = models.CharField(max_length=10, choices=TYPE, default='text')
    body       = models.TextField(blank=True)
    image      = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    # Reply thread
    reply_to   = models.ForeignKey('self', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='replies')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.body[:40]}"


# ── Call ──────────────────────────────────────────────────────────
class Call(models.Model):
    TYPE   = [('audio', 'Audio'), ('video', 'Video')]
    STATUS = [('missed', 'Missed'), ('answered', 'Answered'), ('declined', 'Declined')]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat       = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='calls')
    caller     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='initiated_calls')
    call_type  = models.CharField(max_length=10, choices=TYPE, default='audio')
    status     = models.CharField(max_length=10, choices=STATUS, default='missed')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'calls'
        ordering = ['-started_at']

    @property
    def duration_seconds(self):
        if self.ended_at and self.started_at:
            return int((self.ended_at - self.started_at).total_seconds())
        return 0