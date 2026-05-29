from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def home_view(request):
    return render(request, 'reels/index.html')
from django.urls import path
from django.shortcuts import render

app_name = 'reels'

def placeholder(request):
    return render(request, 'reels/placeholder.html')

urlpatterns = [
    path('', placeholder, name='list'),
]