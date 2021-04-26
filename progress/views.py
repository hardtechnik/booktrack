from datetime import date

from django import forms
from django.forms import widgets
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from basicauth.decorators import basic_auth_required

from .models import BookProgress, Book


class UpdateProgressForm(forms.Form):
    progress = forms.ModelChoiceField(
        queryset=BookProgress.objects.all(),
        widget=widgets.HiddenInput(),
    )
    current_page = forms.IntegerField()
    date = forms.DateField(initial=date.today())
    read_pages = forms.IntegerField()


@method_decorator(basic_auth_required, name='dispatch')
class UpdateProgressView(FormView):
    form_class = UpdateProgressForm
    success_url = reverse_lazy('update_progress')
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, progresses=BookProgress.objects.all())

    def form_valid(self, form):
        progress: BookProgress = form.cleaned_data['progress']
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
        fields = ['title', 'pages']

    def save(self, commit=True):
        book = super().save()
        book.progress.get_or_create(page=0)
        return book


@basic_auth_required
def add_book(request):
    if request.method == 'POST':
        form = AddBookForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect('update_progress')


@basic_auth_required
def delete_book(request, book_id):
    if request.method == 'POST':
        Book.objects.filter(id=book_id).delete()
    return redirect('update_progress')
