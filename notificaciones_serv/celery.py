import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notificaciones_serv.settings')

app = Celery('notificaciones_serv')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()