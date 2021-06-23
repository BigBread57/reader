from django.utils import timezone
from datetime import timedelta, datetime

from django_apscheduler.models import DjangoJobExecution

from accountBd.models import User, Profile
from readerBd.collections import TypeOfDay, Times
from readerBd.models import Event


def my_job():
    """
    :return: Список объектов типа Event для каждого пользователя на один день в количестве 2-х объектов.
    type_time_of_day каждого объекта равен либо output (выходной), либо work (раочий день)
    """

    users = User.objects.values('id')
    # Переменные необходимые для запоминания объетов
    day_list = []  # с типом before_lunch
    evening_list = []  # с типом after_lunch

    # Запускаем цикл который создаст такое количество дней, сколько пользователей в системе
    for days_week in range(0, len(User.objects.all())):
        for i in users:
            # Запоминаем текущий день, когда запущен скрипт и прибавляем к нему по 1 дню в каждой итерации цикла
            date_days_week = timezone.now().date()+timedelta(days=days_week)

            event = Event.objects.filter(date=date_days_week, user_id=i['id']).last()
            profile = Profile.objects.get(user=i['id'])
            # Если текущий день попадает на субботу или воскресенье, то создаем два объекта с типом output (выходной)
            if datetime.weekday(date_days_week) == 5 or datetime.weekday(date_days_week) == 6:
                day_list.append(Event(
                    user_id=i['id'],
                    project=profile.project,
                    date=date_days_week,
                    time_of_respectful_absence_plan=timedelta(0),
                    type_of_day=TypeOfDay.OUTPUT,
                    real_working_hours=timedelta(0),
                    plan_working_hours=timedelta(0)
                ))
            else:
                # Перед созданием объекта мы проверяем, создано ли для данного пользователя событие на текущую дату.
                # Если такого события нет, мы создаем событие с типом work
                if not event:
                    day_list.append(Event(
                        user_id=i['id'],
                        project=profile.project,
                        date=date_days_week,
                        time_of_respectful_absence_plan=timedelta(0),
                        type_of_day=TypeOfDay.WORK,
                        real_working_hours=timedelta(0),
                        plan_working_hours=Times.TIME_WORK_OPERATOR
                    ))
    if day_list:
        Event.objects.bulk_create(day_list)


def delete_old_job_executions(max_age=604_800):
    """Это задание удаляет из базы данных все исполнения заданий apscheduler старше, чем `max_age`"""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)
