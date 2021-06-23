import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_apscheduler.jobstores import DjangoJobStore
from django.conf import settings

from readerBd.services.servicesEvent import delete_old_job_executions, my_job


class Command(BaseCommand):
    help = 'Запускает скрипт по созданию событий автоматически'

    def add_arguments(self, parser):
        parser.add_argument('hour', nargs='?', type=int)
        parser.add_argument('minute', nargs='?', type=int)

    def handle(self, *args, **options):
        """
        Функция описывает триггер, который срабавыет в указнное время и создает по 2 элемента (before_dinner, after_dinner)
        на каждый день для каждого пользователя.
        """
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), 'default')

        if not options.get('hour'):
            if timezone.now().minute == 59:
                default_hour = timezone.now().hour+4
                default_minute = 0
            else:
                default_hour = timezone.now().hour+3
                default_minute = timezone.now().minute+1
        else:
            default_hour = options.get('hour')
            default_minute = options.get('minute')

        scheduler.add_job(
            my_job,
            trigger=CronTrigger(hour=default_hour,
                                minute=default_minute),
            id='my_job',
            # Название функции, которая определяет скрипт, который запускается во время, указанное в trigger
            max_instances=1,
            replace_existing=True,
        )
        logging.info("Added job 'my_job'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week='mon', hour='00', minute='00'
            ),  # Полночь в понедельник перед началом следующей рабочей недели.
            id='delete_old_job_executions',
            max_instances=1,
            replace_existing=True,
        )
        logging.info(
            "Added weekly job: 'delete_old_job_executions'."
        )

        try:
            logging.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logging.info("Stopping scheduler...")
            scheduler.shutdown()
            logging.info("Scheduler shut down successfully!")
