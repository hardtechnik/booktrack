"""booktrack URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path

from progress.views import add_book, delete_book, UpdateProgressView

urlpatterns = [
    path('', UpdateProgressView.as_view(), name='update_progress'),
    path('add-book/', add_book, name='add_book'),
    path('delete-book/<int:book_id>/', delete_book, name='delete_book'),
    # path('admin/', admin.site.urls),
]