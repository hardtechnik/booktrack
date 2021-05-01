from urllib.parse import urlencode, urljoin

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

import requests

from .forms import AddBookForm, UpdateProgressForm
from .models import Book, BookProgress


@login_required(login_url='login')
def profile_view(request, user_id):
    profile = get_object_or_404(User, pk=user_id)
    user_progress = BookProgress.objects.filter(book__user=profile)
    context = {'progresses': user_progress, 'profile': profile}
    return render(request, 'profile.html', context)


@login_required(login_url='login')
@require_http_methods(['POST'])
def update_progress(request, progress_id):
    progress = get_object_or_404(BookProgress, pk=progress_id, book__user=request.user)
    data = request.POST.copy()
    data['progress'] = progress
    form = UpdateProgressForm(data)
    if form.is_valid():
        form.save()
    return redirect('profile', user_id=request.user.id)


@login_required(login_url='login')
def add_book(request):
    if request.method == 'POST':
        data = request.POST.copy()
        data['user'] = request.user.id
        form = AddBookForm(data)
        if form.is_valid():
            form.save()
    return redirect('profile', user_id=request.user.id)


@login_required(login_url='login')
def delete_book(request, book_id):
    if request.method == 'POST':
        Book.objects.filter(id=book_id, user=request.user).delete()
    return redirect('profile', user_id=request.user.id)


def oauth_request(request):
    params = urlencode({
        'client_id': settings.VK_CLIENT_ID,
        'redirect_uri': _get_redirect_uri(request),
        'display': 'popup',
        'scope': 1 << 22,
        'response_type': 'code',
    })
    return redirect(f'https://oauth.vk.com/authorize?{params}')


def oauth_callback(request):
    code = request.GET['code']
    response = requests.get('https://oauth.vk.com/access_token', params={
        'client_id': settings.VK_CLIENT_ID,
        'client_secret': settings.VK_SECRET_KEY,
        'redirect_uri': _get_redirect_uri(request),
        'code': code,
    })
    email = response.json()['email']
    user, _ = get_user_model().objects.get_or_create(email=email)
    login(request, user)
    return redirect('profile', user_id=user.id)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile', user_id=request.user.id)
    return render(request, 'login.html')


def _get_redirect_uri(request):
    return urljoin(f'https://{request.get_host()}', reverse('oauth_callback'))
