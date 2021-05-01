from datetime import date, timedelta

from django.contrib.auth.models import User
from django.urls import reverse

import pytest

from .forms import UpdateProgressForm
from .models import Book, BookProgress, DailyProgress


@pytest.fixture
def user(db):
    return User.objects.create(email='john.doe@mail.com')


@pytest.fixture
def book(user):
    book = Book.objects.create(title='Bible', pages=1563, user=user)
    book.progress.get_or_create(page=0)
    return book


@pytest.fixture
def user_client(client, user):
    client.force_login(user=user)
    client.user = user
    return client


def test_create_progress(db, client, user):
    today = date.today()
    book = Book.objects.create(title='Bible', pages=1563, user=user)
    progress = BookProgress.objects.create(book=book, page=616)
    assert progress.expected_end is None

    today_progress = DailyProgress.objects.create(book_progress=progress, date=today, read_pages=15)
    assert str(today_progress) == f'{book.title}: read {today_progress.read_pages} on {today}'
    days = (book.pages - progress.page) // today_progress.read_pages
    assert progress.expected_end == today + timedelta(days=days)


@pytest.fixture(params=[
    'profile',
    'update_progress',
    'add_book',
    'delete_book',
])
def private_url(request, user, book):
    kwargs = {}
    if request.param == 'profile':
        kwargs = {'user_id': user.id}
    if request.param == 'update_progress':
        kwargs = {'progress_id': book.progress.get().id}
    if request.param == 'delete_book':
        kwargs = {'book_id': book.id}
    return reverse(request.param, kwargs=kwargs)


def test_login_required(client, private_url, user):
    response = client.get(private_url, follow=True)
    assert response.resolver_match.view_name == 'login'
    assert response.status_code == 200


def test_profile_page(user_client):
    profile_url = reverse('profile', kwargs={'user_id': user_client.user.id})
    response = user_client.get(profile_url, follow=True)
    assert b'Add a book' in response.content

    book_data = {'title': 'Bible', 'pages': 1564}
    response = user_client.post(reverse('add_book'), data=book_data, follow=True)
    assert response.resolver_match.view_name == 'profile'
    assert response.status_code == 200
    assert b'Bible' in response.content

    bible = Book.objects.get(**book_data)
    progress = bible.progress.get()
    progress_data = {'current_page': 400, 'read_pages': 15, 'date': '2021-05-01'}
    update_progress_url = reverse('update_progress', kwargs={'progress_id': progress.id})
    response = user_client.post(update_progress_url, progress_data, follow=True)
    assert response.resolver_match.view_name == 'profile'
    assert response.status_code == 200
    assert f'415/{bible.pages}'.encode('utf-8') in response.content
    assert b'Current tempo is 15.0 pages per day' in response.content

    delete_book_url = reverse('delete_book', kwargs={'book_id': bible.id})
    response = user_client.post(delete_book_url, follow=True)
    assert response.resolver_match.view_name == 'profile'
    assert response.status_code == 200
    assert b'Bible' not in response.content


def test_update_progress_form(book):
    data = {
        'progress': book.progress.get(),
        'current_page': 100,
        'read_pages': 10,
        'date': '2021-05-01',
    }

    def expect_current_page_is(expected_pages, data):
        form = UpdateProgressForm(data)
        assert form.is_valid()
        progress = form.save()
        progress.refresh_from_db()
        assert progress.page == expected_pages

    expect_current_page_is(110, data)
    data['current_page'] = 100500
    expect_current_page_is(book.pages, data)

    data['current_page'] = book.pages
    data['read_pages'] = 100
    expect_current_page_is(book.pages, data)

    data['current_page'] = -101
    form = UpdateProgressForm(data)
    assert not form.is_valid()

    data['current_page'] = 101
    data['read_pages'] = -32
    form = UpdateProgressForm(data)
    assert not form.is_valid()
