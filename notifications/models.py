from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
import uuid


class Notification(models.Model):
    TYPE = [
        ('like',          'Like'),
        ('comment',       'Comment'),
        ('follow',        'Follow'),
        ('follow_request','Follow Request'),
        ('friend_request','Friend Request'),
        ('mention',       'Mention'),
        ('message',       'Message'),
        ('call',          'Call'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='notifications')
    sender      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='sent_notifications', null=True, blank=True)
    notif_type  = models.CharField(max_length=20, choices=TYPE)
    text        = models.CharField(max_length=255, blank=True)

    # Optional object references
    post_id     = models.UUIDField(null=True, blank=True)
    comment_id  = models.UUIDField(null=True, blank=True)
    chat_id     = models.UUIDField(null=True, blank=True)

    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notif_type} → {self.recipient}"

    def get_url(self):
        if self.notif_type in ('like', 'comment', 'mention') and self.post_id:
            return f'/posts/{self.post_id}/'
        if self.notif_type in ('follow', 'follow_request', 'friend_request') and self.sender:
            return f'/users/{self.sender.username}/'
        if self.notif_type in ('message', 'call') and self.chat_id:
            return f'/chats/{self.chat_id}/'
        return '/'

    def get_icon(self):
        icons = {
            'like':           '♥',
            'comment':        '💬',
            'follow':         '👤',
            'follow_request': '🔒',
            'friend_request': '🤝',
            'mention':        '@',
            'message':        '✉',
            'call':           '📞',
        }
        return icons.get(self.notif_type, '🔔')