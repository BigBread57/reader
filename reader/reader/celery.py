import os

from celery import Celery

from celery.schedules import crontab

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reader.settings.local')
except ModuleNotFoundError:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reader.settings.common')

app = Celery('reader')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Загрузить модули задач из всех зарегистрированных приложений Django
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'add_day': {
        'task': 'readerBd.tasks.add_day',
        'schedule': crontab(hour=15, minute=30),
    },
    'close_day': {
        'task': 'readerBd.tasks.close_day',
        'schedule': crontab(hour=23, minute=45),
    },
    'recalculation_day': {
        'task': 'readerBd.tasks.recalculation_day',
        'schedule': crontab(hour=23, minute=50),
    },
}
