from datetime import date, timedelta

from .models import Book, BookProgress, DailyProgress


def test_create_progress(db, client):
    today = date.today()
    book = Book.objects.create(title='Bible', pages=1563)
    progress = BookProgress.objects.create(book=book, page=616)
    assert progress.expected_end is None

    today_progress = DailyProgress.objects.create(book_progress=progress, date=today, read_pages=15)
    assert str(today_progress) == f'{book.title}: read {today_progress.read_pages} on {today}'
    days = (book.pages - progress.page) // today_progress.read_pages
    assert progress.expected_end == today + timedelta(days=days)

    response = client.get('/')
    content = response.content.decode('utf-8')
    assert response.status_code == 200
    assert book.title in content
    assert progress.expected_end.strftime('%B %d, %Y') in content
