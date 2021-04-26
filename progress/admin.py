from django.contrib import admin

from .models import Book, BookProgress


class ProgressInline(admin.TabularInline):
    model = BookProgress
    max_num = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    inlines = [ProgressInline]
