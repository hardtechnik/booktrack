import django_heroku

from .base import *  # noqa: F403, F401


DEBUG = False

django_heroku.settings(locals())
