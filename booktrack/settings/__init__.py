import os


environment = os.getenv('ENVIRONMENT', 'dev')
if environment == 'production':
    from .production import *  # noqa: F403, F401
else:
    from .base import *  # noqa: F403, F401
