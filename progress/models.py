from datetime import date, timedelta

from django.db import models
from django.db.models import Avg


class Book(models.Model):
    title = models.CharField(max_length=255)
    pages = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class BookProgress(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='progress')
    page = models.PositiveIntegerField()

    @property
    def expected_end(self):
        avg_pages = self.daily.aggregate(avg_pages=Avg('read_pages'))['avg_pages']
        if not avg_pages:
            return None
        need_to_read = self.book.pages - self.page
        expected_days = need_to_read // avg_pages
        return date.today() + timedelta(days=expected_days)

    def __str__(self):
        return f'{self.book}: {self.page}/{self.book.pages}'


class DailyProgress(models.Model):
    book_progress = models.ForeignKey(BookProgress, on_delete=models.CASCADE, related_name='daily')
    date = models.DateField()
    read_pages = models.PositiveIntegerField(0)

    def __str__(self):
        return f'{self.book_progress.book}: read {self.read_pages} on {self.date}'
