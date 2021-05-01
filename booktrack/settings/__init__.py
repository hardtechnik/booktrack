import os

environment = os.getenv('ENVIRONMENT', 'dev')
if environment == 'production':
    from .production import *
else:
    from .base import *
