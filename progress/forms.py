from datetime import date

from django import forms
from django.forms import widgets

from progress.models import BookProgress, Book


class UpdateProgressForm(forms.Form):
    progress = forms.ModelChoiceField(
        queryset=BookProgress.objects.all(),
        widget=widgets.HiddenInput(),
    )
    current_page = forms.IntegerField(min_value=1)
    date = forms.DateField(initial=date.today())
    read_pages = forms.IntegerField(min_value=1)

    def save(self):
        progress = self.cleaned_data['progress']
        current_page = self.cleaned_data['current_page'] + self.cleaned_data['read_pages']
        progress.page = min(current_page, progress.book.pages)
        progress.save(update_fields=['page'])
        progress.daily.update_or_create(
            date=self.cleaned_data['date'],
            defaults={'read_pages': self.cleaned_data['read_pages']},
        )
        return progress


class AddBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'pages', 'user']

    def save(self, commit=True):
        book = super().save()
        book.progress.get_or_create(page=0)
        return book
