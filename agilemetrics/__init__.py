from __future__ import absolute_import, unicode_literals

# This will make sure the app is always imported when
# Django starts so Celery tasks are recognized.
from .celery import app as celery_app

__all__ = ('celery_app',)