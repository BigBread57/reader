import datetime

from django.db.models import Max, Min, Sum
from django.utils.timezone import utc

from accountBd.collections import UserPosition, NumberAppeal, UserStatus
from accountBd.models import Profile
from readerBd.collections import TypeOfDay, Times
from readerBd.models import Event


# Функция позвоялет расчитывать время переработки пользователя
def overtime_calculation(time_entry, time_exit, user, day):
    """
    :param time_entry: переменная типа datetime без microsecond, содержащая время и дату входа
    :param time_exit: переменная типа datetime без microsecond, содержащая время и дату выхода
    :param user: объект пользователя, которому принадлежит событие
    :param day: объект события, которому принадлежит control_time
    :return: Возвращает переменную overtime типа timedelta, которая содержит информацию о времени переработки
    """

    # Ниже идут переменные для подсчета разницы между фактическим временем входа и выхода и временем рабочего дня
    # по плану. Необходимо для контролирования переработок.
    overtime = datetime.timedelta(0)

    # Переменные для приведение установленного распорядка рабочего дня, к текущей дате для операторов и персонала.

    # Расчет показателей для операторов с учетом дня (для возможности вычитания и расчетов)
    # 9:00 текущего дня
    datetime_entry_morning_operator = datetime.datetime.combine(time_entry.date(),
                                                                Times.TIME_ENTRY_MORNING_OPERATOR, tzinfo=utc)
    # 13:00 текущего дня
    datetime_exit_morning_operator = datetime.datetime.combine(time_exit.date(),
                                                               Times.TIME_EXIT_MORNING_OPERATOR, tzinfo=utc)
    # 15:00 текущего дня
    datetime_entry_evening_operator = datetime.datetime.combine(time_entry.date(),
                                                                Times.TIME_ENTRY_EVENING_OPERATOR, tzinfo=utc)
    # 17:00 текущего дня
    datetime_exit_evening_operator = datetime.datetime.combine(time_exit.date(),
                                                               Times.TIME_EXIT_EVENING_OPERATOR, tzinfo=utc)

    # Расчет показателей для персонала с учетом дня (для возможности вычитания и расчетов)
    # 9:00 текущего дня
    datetime_entry_morning_personal = datetime.datetime.combine(time_entry.date(),
                                                                Times.TIME_ENTRY_MORNING_PERSONAL, tzinfo=utc)
    # 18:00 текущего дня
    datetime_exit_evening_personal = datetime.datetime.combine(time_exit.date(),
                                                               Times.TIME_EXIT_EVENING_PERSONAL, tzinfo=utc)

    # Переменные, приведеные ниже необходимы для осуществления контроля времени переработки.
    # Название переменной формируется из название константы, например Times.TIME_ENTRY_MORNING_OPERATOR
    # и действи пользователя (вход - entry или выход - exit). Перемнные имеют тип - timedelta

    # Переменные необходимы для подсчета времени переработки, когда оператор прибыл в лабораторию до 9:00
    # Из 9:00 вычитаем время входа
    datetime_entry_morning_operator_difference_entry = datetime_entry_morning_operator - time_entry

    # Переменная необходима для подсчета времени переработки, когда оператор уходит из лаборатории после 13:00
    # Из текущего времени вхоа и выхода вычитаем 13:00
    datetime_exit_morning_operator_difference_entry = time_entry - datetime_exit_morning_operator
    datetime_exit_morning_operator_difference_exit = time_exit - datetime_exit_morning_operator

    # Переменные необходимы для подсчета переработки если оператор пришел с 13:00 до 15:00
    # Из 15:00 вычитаем текущее время входа и выхода
    datetime_entry_evening_operator_difference_entry = datetime_entry_evening_operator - time_entry
    datetime_entry_evening_operator_difference_exit = datetime_entry_evening_operator - time_exit

    # Переменная необходима для подсчета времени переработки, когда оператор уходит из лаборатории после 17:00
    # Из текущего времени выхода вычитаем 17:00
    datetime_exit_evening_operator_difference_exit = time_exit - datetime_exit_evening_operator

    # Для персонала дополнителные переменные не вводятся по скольку время обеда они могут проводить на рабочем месте
    # и оно не засчитывается в переработку.
    datetime_entry_morning_personal_difference = datetime_entry_morning_personal - time_entry
    datetime_exit_evening_personal_difference = time_exit - datetime_exit_evening_personal

    # Проверяем кто входит в лабораторию, если оператор, то:
    if user.profile.position in (UserPosition.OPERATOR, UserPosition.SENIOR_OPERATOR):
        if day.type_of_day == TypeOfDay.WORK:

            # Проверяем если время входа и выхода оператора меньше чем 9:00 (то есть пользователь работал до начала
            # рабочего дня), и его разница времени входа и 9:00 больше чем время, отведенное для резерва (10 минут)
            if time_entry < datetime_entry_morning_operator and time_exit < datetime_entry_morning_operator and \
                    datetime_entry_morning_operator_difference_entry > Times.TIME_DELAY:
                overtime = time_exit - time_entry

            # Проверяем, ели оператор пришел до 9:00 и его разница времени входа и 9:00 больше чем время,
            # отведенное для резерва (10 минут), и ушел оператор до 13:00
            elif time_entry < datetime_entry_morning_operator < time_exit <= datetime_exit_morning_operator and \
                    datetime_entry_morning_operator_difference_entry > Times.TIME_DELAY:
                overtime = datetime_entry_morning_operator_difference_entry

            # Проверяем если оператор пришел до 9:00 и ушел c 13:00 до 15:00 и его разница времени
            # входа и 9:00 больше чем время, отведенное для резерва (10 минут)
            elif time_entry < datetime_entry_morning_operator and \
                    datetime_entry_morning_operator_difference_entry > Times.TIME_DELAY and \
                    datetime_exit_morning_operator < time_exit <= datetime_entry_evening_operator:
                overtime = datetime_entry_morning_operator_difference_entry + \
                           datetime_exit_morning_operator_difference_exit

            # Проверяем если оператор пришел после 9:00 и ушел c 13:00 до 15:00 и его разница времени
            # выхода и 13:00 больше чем время, отведенное для резерва (10 минут)
            elif datetime_entry_morning_operator <= time_entry < datetime_exit_morning_operator \
                    < time_exit <= datetime_entry_evening_operator and \
                    datetime_exit_morning_operator_difference_exit > Times.TIME_DELAY:
                overtime = datetime_exit_morning_operator_difference_exit

            # Проверяем если оператор пришел и ушел c 13:00 до 15:00
            elif datetime_exit_morning_operator_difference_entry > Times.TIME_DELAY and \
                    datetime_exit_morning_operator < time_entry < datetime_entry_evening_operator and \
                    datetime_entry_evening_operator_difference_exit < datetime.timedelta(0) and \
                    datetime_exit_morning_operator < time_exit <= datetime_entry_evening_operator:
                overtime = time_exit - time_entry

            # Проверяем если оператор пришел с 13:00 до 15:00 и ушел до 17:00
            elif datetime_exit_morning_operator < time_entry < datetime_entry_evening_operator and \
                    datetime_entry_evening_operator_difference_entry > Times.TIME_DELAY and \
                    datetime_entry_evening_operator_difference_exit < datetime.timedelta(0) and \
                    datetime_exit_evening_operator_difference_exit < datetime.timedelta(0) and \
                    time_exit <= datetime_exit_evening_operator:
                overtime = datetime_entry_evening_operator_difference_entry

            # Проверяем если оператор пришел с 13:00 до 15:00 и ушел после 17:00
            elif datetime_exit_morning_operator < time_entry < datetime_entry_evening_operator and \
                    datetime_entry_evening_operator_difference_entry > Times.TIME_DELAY and \
                    datetime_exit_evening_operator_difference_exit > datetime.timedelta(0) and \
                    datetime_exit_evening_operator < time_exit:
                overtime = datetime_entry_evening_operator_difference_entry + \
                           datetime_exit_evening_operator_difference_exit

            # Проверяем если оператор пришел с 15:00 и ушел после 17:00
            elif datetime_entry_evening_operator <= time_entry < datetime_exit_evening_operator < time_exit and \
                    datetime_exit_evening_operator_difference_exit > datetime.timedelta(0):
                overtime = datetime_exit_evening_operator_difference_exit

            # Проверяем если оператор пришел с 17:00
            elif datetime_exit_evening_operator <= time_entry and \
                    datetime_exit_evening_operator_difference_exit > datetime.timedelta(0):
                overtime = time_exit - time_entry

            # Проверяем если оператор пришел до 9:00 и ушел после 17:00
            elif time_entry < datetime_entry_morning_operator and datetime_exit_evening_operator < time_exit:
                overtime = datetime_entry_morning_operator_difference_entry +\
                           datetime_exit_evening_operator_difference_exit + datetime.timedelta(hours=2)

        else:
            overtime = time_exit - time_entry

    # Если персонал, то проверяем всего 2 события:
    else:
        if day.type_of_day == TypeOfDay.WORK:
            if datetime_entry_morning_personal_difference > Times.TIME_DELAY:
                overtime += datetime_entry_morning_personal_difference
            if datetime_exit_evening_personal_difference > Times.TIME_DELAY:
                overtime += datetime_exit_evening_personal_difference
        else:
            overtime = time_exit - time_entry
    return overtime


def change_appeal(priority_duty):
    """
    :param priority_duty: Объект OfferOfDuty, который содержит информацию о текущем дежурном призыве
    :return: Возвращает priority_duty, содержащую информацию о призыве, который должен дежурить
    """
    # Получаем профили тех пользователй, которые не демобилизованы
    qs = Profile.objects.filter(position__in=(UserPosition.OPERATOR,
                                              UserPosition.SENIOR_OPERATOR)).exclude(status=UserStatus.DEMOB)
    # Переменные необходимы для проверки 2х призывов в системе и корректного расчета призыва для дежурства.
    # Один призыв находится в системе, когда второй призыв уходит на дембель
    min_year_appeal = qs.aggregate(min_year=Min('year_appeal'))['min_year']
    max_year_appeal = qs.aggregate(max_year=Max('year_appeal'))['max_year']

    min_number_appeal = qs.aggregate(min_number_appeal=Min('number_appeal'))['min_number_appeal']
    max_number_appeal = qs.aggregate(max_number_appeal=Max('number_appeal'))['max_number_appeal']

    # Условия для смены приоритета дежурства (1 проверка нужна, для того чтобы возвращать тот же самый призыв,
    # когда он остается один)
    if min_number_appeal != max_number_appeal:
        if priority_duty.number_appeal == NumberAppeal.ONE:
            priority_duty.number_appeal = NumberAppeal.TWO
            priority_duty.year_appeal = min_year_appeal
        else:
            if priority_duty.year_appeal == min_year_appeal:
                priority_duty.number_appeal = NumberAppeal.ONE
                priority_duty.year_appeal = min_year_appeal
            else:
                priority_duty.number_appeal = NumberAppeal.ONE
                priority_duty.year_appeal = max_year_appeal
    return priority_duty


def calculation_time_variable(day):
    # Список хранит id всех событий, которые относятся к дню
    list_day_event_id = []
    # Переменные храянят временные значия количесва общего времени в лаборатории и переработки
    time_difference = datetime.timedelta(0)
    overtime = datetime.timedelta(0)

    # Получаем все time_difference и overtime из control_time, которые принадлежат текущему дню
    # и их сумму заносим в переменные
    for control_time in day.control_times.all():
        time_difference += control_time.time_difference
        overtime += control_time.overtime

    if day.type_of_day == TypeOfDay.WORK:
        day.real_working_hours = time_difference - overtime
        day.real_overtime = overtime
    else:
        day.real_working_hours = datetime.timedelta(0)
        day.real_overtime = overtime

    # Получаем id событий, которые относятся к текущему дню
    for day_event_id in day.event.all().values('id'):
        list_day_event_id.append(day_event_id['id'])

    # Проверяем есть ли события, если есть то разделяем такие события на уважительные и не уважительные
    if list_day_event_id:
        event_respectful_absence = Event.objects.filter(id__in=list_day_event_id, respectful_absence=True).aggregate(
            sum_time=Sum('time_plan'))['sum_time']

        event_not_respectful_absence = \
            Event.objects.filter(id__in=list_day_event_id, respectful_absence=False).aggregate(
                sum_time=Sum('time_plan'))['sum_time']

        if not event_respectful_absence:
            event_respectful_absence = datetime.timedelta(0)
        if not event_not_respectful_absence:
            event_not_respectful_absence = datetime.timedelta(0)

        # Рабочее время + уважительное время событий + не уважительное время событий
        count_time_all = event_respectful_absence + event_not_respectful_absence + day.real_working_hours

        # Уважительное время событий + не уважительное время событий
        events_all_time = event_respectful_absence + event_not_respectful_absence

        # Если плановое время работы больше фактического времени работы, то в уважительное время отсуствия заносим,
        # (то время что указано в событиях), а в неуважительное, (то что указано в событиях и время которое осталось
        # из планового времени за вычетом фактически отработанного времени)
        if day.plan_working_hours >= count_time_all:
            day.time_of_respectful_absence_fact = event_respectful_absence
            day.time_of_not_respectful_absence_fact = day.plan_working_hours - count_time_all + event_not_respectful_absence

        # Если плановое время работы меньше фактического времени работы, то проверяем
        elif day.plan_working_hours < count_time_all:

            # Если уважительное время события равно 0, то оставшееся время записывается в неуважительное
            if event_respectful_absence == datetime.timedelta(0) and \
                    event_not_respectful_absence != datetime.timedelta(0):
                day.time_of_respectful_absence_fact = datetime.timedelta(0)
                day.time_of_not_respectful_absence_fact = day.plan_working_hours - day.real_working_hours

            # Если не уважительное время события равно 0, то оставшееся время записывается в уважительное
            elif event_not_respectful_absence == datetime.timedelta(0) and \
                    event_respectful_absence != datetime.timedelta(0):
                day.time_of_respectful_absence_fact = day.plan_working_hours - day.real_working_hours
                day.time_of_not_respectful_absence_fact = datetime.timedelta(0)

            # Если не уважительное и уважительное время не равно нулю, то записывается в оба времени пропорционально,
            # тому времени, которое указано в плановом времени события. То есть если уважительных событий было на
            # 2 часа, а неуажиметльных на 1, то пропрции буту 66,6 к уважительным и 33,3 к неуважительным
            elif event_not_respectful_absence != datetime.timedelta(0) and \
                    event_respectful_absence != datetime.timedelta(0):
                day.time_of_respectful_absence_fact = ((event_respectful_absence / events_all_time) *
                                                       (day.plan_working_hours - day.real_working_hours))
                day.time_of_not_respectful_absence_fact = (day.plan_working_hours - day.real_working_hours -
                                                           day.time_of_respectful_absence_fact)

    return day
