from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotAllowed


@login_required
def home_view(request):
    return render(request, 'chats/index.html')


@login_required
def start_dm_view(request, username):
    return redirect('chats:home')


@login_required
def friend_request_view(request, username):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    if username == request.user.username:
        return JsonResponse({'status': 'error', 'message': 'Cannot add yourself'}, status=400)
    return JsonResponse({'status': 'sent'})
