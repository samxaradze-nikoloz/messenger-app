from .models import Notification


def notify(recipient, sender, notif_type, text='', post_id=None, comment_id=None, chat_id=None):
    """Create a notification. Silently skips self-notifications."""
    if recipient == sender:
        return None
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notif_type=notif_type,
        text=text,
        post_id=post_id,
        comment_id=comment_id,
        chat_id=chat_id,
    )