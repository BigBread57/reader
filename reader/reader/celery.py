import os

from celery import Celery

from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reader.settings.common')

app = Celery('reader')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Загрузить модули задач из всех зарегистрированных приложений Django
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'add_day': {
        'task': 'readerBd.tasks.add_day',
        'schedule': crontab(hour=10, minute=49),
    },
}
