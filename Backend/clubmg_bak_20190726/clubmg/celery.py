#coding: utf-8

from __future__ import absolute_import, unicode_literals

import os

from celery import Celery, platforms
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clubmg.settings')
from django.conf import settings


platforms.C_FORCE_ROOT = True

app = Celery('clubmg')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

