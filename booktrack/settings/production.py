import django_heroku

from .base import *  # noqa: F403, F401


django_heroku.settings(locals())
