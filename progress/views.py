from datetime import date
from urllib.parse import urlencode, urljoin

from django import forms
from django.conf import settings
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.forms import widgets
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView
import requests

from .models import BookProgress, Book


class UpdateProgressForm(forms.Form):
    progress = forms.ModelChoiceField(
        queryset=BookProgress.objects.all(),
        widget=widgets.HiddenInput(),
    )
    current_page = forms.IntegerField()
    date = forms.DateField(initial=date.today())
    read_pages = forms.IntegerField()


@method_decorator(login_required(login_url='login'), name='dispatch')
class UpdateProgressView(FormView):
    form_class = UpdateProgressForm
    template_name = 'index.html'

    def get_success_url(self):
        return reverse('update_progress', kwargs={'user_id': self.request.user.id})

    def get_context_data(self, **kwargs):
        user_progress = BookProgress.objects.filter(book__user=self.request.user)
        return super().get_context_data(**kwargs, progresses=user_progress)

    def form_valid(self, form):
        progress: BookProgress = form.cleaned_data['progress']
        if not progress.book.user == self.request.user:
            raise Http404
        progress.page = form.cleaned_data['current_page'] + form.cleaned_data['read_pages']
        progress.save(update_fields=['page'])
        progress.daily.update_or_create(
            date=form.cleaned_data['date'],
            defaults={'read_pages': form.cleaned_data['read_pages']},
        )
        return super().form_valid(form)


class AddBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'pages', 'user']

    def save(self, commit=True):
        book = super().save()
        book.progress.get_or_create(page=0)
        return book


@login_required(login_url='login')
def add_book(request):
    if request.method == 'POST':
        data = request.POST.copy()
        data['user'] = request.user.id
        form = AddBookForm(data)
        if form.is_valid():
            form.save()
    return redirect('update_progress', user_id=request.user.id)


@login_required(login_url='login')
def delete_book(request, book_id):
    if request.method == 'POST':
        Book.objects.filter(id=book_id, user=request.user).delete()
    return redirect('update_progress', user_id=request.user.id)


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
    return redirect('update_progress', user_id=user.id)


class LoginView(TemplateView):
    template_name = 'login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('update_progress', user_id=request.user.id)
        return super().dispatch(request, *args, **kwargs)


def _get_redirect_uri(request):
    return urljoin(f'https://{request.get_host()}', reverse('oauth_callback'))
