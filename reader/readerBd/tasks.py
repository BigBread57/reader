import logging
import datetime

from django.utils import timezone
from django.utils.timezone import utc

from reader.celery import app

logger = logging.getLogger(__name__)


@app.task
def add_day():
    """
    Функция которая автоматически создает дни для всех пользователей системы

    :return: Список объектов типа Day для каждого пользователя на неделю
    """

    from readerBd.collections import TypeOfDay, Times
    from readerBd.models import Day
    from accountBd.models import User
    from accountBd.collections import UserPosition
    from accountBd.collections import UserStatus

    # Ищем пользователей, у которых статус не демобилизиван
    users = list(User.objects.exclude(profile__status=UserStatus.DEMOB))

    # Переменная необходимая для запоминания созданных объетов
    day_list = []

    # Запускаем цикл который создаст 7 дней
    for days_week in range(0, 6):
        for user in users:
            # Запоминаем текущий день, когда запущен скрипт и прибавляем к нему по 1 дню в каждой итерации цикла
            date_days_week = timezone.now().date() + datetime.timedelta(days=days_week)

            # Перед созданием объекта мы проверяем, создан ли для данного пользователя день с текущей датой.
            # Если такого дня нет, создаем его
            try:
                day = Day.objects.get(date=date_days_week, user_id=user.id)
            except Day.DoesNotExist:
                # Если текущий день попадает на субботу или воскресенье, то создаем объект с типом output (выходной)
                if datetime.datetime.weekday(date_days_week) in (5, 6):
                    day_list.append(Day(
                        user_id=user.id,
                        project=user.profile.project,
                        date=date_days_week,
                        type_of_day=TypeOfDay.OUTPUT,
                        real_working_hours=datetime.timedelta(0),
                        plan_working_hours=datetime.timedelta(0)
                    ))
                else:
                    # Проверяем статус пользователя и запоминаем его плановое количество рабочего времени
                    if user.profile.position in (UserPosition.OPERATOR, UserPosition.SENIOR_OPERATOR):
                        plan_working_hours = Times.TIME_WORK_OPERATOR
                    else:
                        plan_working_hours = Times.TIME_WORK_PERSONAL

                    day_list.append(Day(
                        user_id=user.id,
                        project=user.profile.project,
                        date=date_days_week,
                        type_of_day=TypeOfDay.WORK,
                        real_working_hours=datetime.timedelta(0),
                        plan_working_hours=plan_working_hours
                    ))

    if day_list:
        Day.objects.bulk_create(day_list)


@app.task
def close_day():
    """
    Функция по закрытию control_time, где отсутсвует время выхода

    :return: Добавляет время выхода в те объекты ControlTime, которые без time_exit, рассчитывает time_difference
    и overtime. Обновляет базу данных.
    """

    from accountBd.collections import UserPosition
    from readerBd.models import ControlTime
    from api.public.readerBd.utils import overtime_calculation
    from readerBd.collections import Times, TypeOfDay

    # Получаем список всех control_time где нет времени выхода
    control_times = list(ControlTime.objects.filter(time_exit__isnull=True))

    for control_time in control_times:

        if control_time.day.user.profile.position in (UserPosition.OPERATOR, UserPosition.SENIOR_OPERATOR):
            control_time.time_exit = datetime.datetime.combine(control_time.time_entry.date(),
                                                               Times.TIME_EXIT_EVENING_OPERATOR, tzinfo=utc)
        else:
            control_time.time_exit = datetime.datetime.combine(control_time.time_entry.date(),
                                                               Times.TIME_EXIT_EVENING_PERSONAL, tzinfo=utc)

        # Устанавливаем общее время нахождения в лаборатории
        control_time.time_difference = control_time.time_exit - control_time.time_entry

        # Рассчитываем время переработки
        if control_time.day.type_of_day == TypeOfDay.WORK:
            control_time.overtime = overtime_calculation(control_time.time_entry,
                                                         control_time.time_exit,
                                                         control_time.day.user,
                                                         control_time.day)
        else:
            control_time.overtime = control_time.time_difference

        control_time.save()


@app.task
def recalculation_day():
    """
    Функция по перерасчету данных в объекте Day

    :return: Добавляет в объект Day значения в поля real_working_hours, real_overtime
    time_of_respectful_absence_fact и time_of_not_respectful_absence_fact
    """

    from api.public.readerBd.utils import calculation_time_variable
    from readerBd.models import Day

    days = list(Day.objects.filter(date=timezone.now().date()))

    for day in days:
        rec_day = calculation_time_variable(day)
        rec_day.save()
