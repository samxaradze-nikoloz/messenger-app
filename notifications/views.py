from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification


@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender').order_by('-created_at')[:60]

    # Mark all as read
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)

    return render(request, 'notifications/list.html', {'notifications': notifs})


@login_required
def unread_count_view(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
@require_POST
def mark_read_view(request, notif_id):
    Notification.objects.filter(id=notif_id, recipient=request.user).update(is_read=True)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def clear_all_view(request):
    Notification.objects.filter(recipient=request.user).delete()
    return JsonResponse({'ok': True})