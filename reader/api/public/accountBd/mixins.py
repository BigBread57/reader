from django.db.models import Sum, Q, Prefetch, Value, DurationField, F, When, Case
from django.utils import timezone

from readerBd.models import Day


class StatisticUserMixin:
    """
    Класс позволяет осуществлять расчет статистической информации по пользователям в совокупности и по отдельности,
    позволяет применять фильтры к событиям по датам
    """

    def get_queryset(self):
        query = Q()
        query_hours = Q(user__days__user_id=F('user_id'))
        # Получаем атрибут запроса (данные из фильтра)
        time_entry = self.request.query_params.get('time_entry')
        time_exit = self.request.query_params.get('time_exit')
        # Если начальная дата в фильтре указана то
        if time_entry:
            # Формируем первый запрос, где даты больше или равны,
            # той дате, что указано в фильтре. Первый запрос нужен для Prefetch
            query = Q(query & Q(date__gte=time_entry))
            # Формируем второй запрос,
            # с таким же условием, второй запрос нужен для агрегации
            query_hours = Q(query_hours & Q(user__days__date__gte=time_entry))
        # Тоже самое делаем для второй даты
        if time_exit:
            query = Q(query & Q(date__lte=time_exit))
            query_hours = Q(query_hours & Q(user__days__date__lte=time_exit))
        # Указываем текущую дату, чтобы если события созданы на будущие числа, они не учитывались в статистике
        if not time_entry and not time_exit:
            query = Q(query & Q(date__lte=timezone.now().date()))
            query_hours = Q(query_hours & Q(user__days__date__lte=timezone.now().date()))

        qs = super().get_queryset().prefetch_related(
            Prefetch('user__days', queryset=Day.objects.filter(query).distinct()))

        qs_time_schedule = Sum('user__days__plan_working_hours', filter=query_hours)
        qs_time_work = Sum('user__days__real_working_hours', filter=query_hours)
        qs_real_overtime = Sum('user__days__real_overtime', filter=query_hours)
        qs_time_of_respectful_absence_fact = Sum('user__days__time_of_respectful_absence_fact', filter=query_hours)
        qs_time_of_not_respectful_absence_fact = Sum('user__days__time_of_not_respectful_absence_fact',
                                                     filter=query_hours)

        return qs.annotate(
            time_schedule=qs_time_schedule,  # Время работы по графику
            # Время уважительных прогулов (планируемое)
            time_work=qs_time_work,  # Время работы по факту
            real_overtime=qs_real_overtime,  # Время переработки по факту
            time_of_respectful_absence_fact=qs_time_of_respectful_absence_fact,
            time_of_not_respectful_absence_fact=qs_time_of_not_respectful_absence_fact
        )


class StatisticProjectMixin:
    """
    Класс позволяет осуществлять расчет статистической информации по проектам, позволяет применять фильтры к событиям
    по датам
    """

    def get_queryset(self):
        query = Q()
        query_hours = Q(days__project_id=F('id'))
        # Получаем атрибут запроса (данные из фильтра)
        time_entry = self.request.query_params.get('time_entry')
        time_exit = self.request.query_params.get('time_exit')
        # Если начальная дата в фильтре указана то
        if time_entry:
            # Формируем первый запрос, где даты больше или равны,
            # той дате, что указано в фильтре. Первый запрос нужен для Prefetch
            query = Q(query & Q(date__gte=time_entry))
            # Формируем второй запрос,
            # с таким же условием, второй запрос нужен для агрегации
            query_hours = Q(query_hours & Q(days__date__gte=time_entry))
        # Тоже самое делаем для второй даты
        if time_exit:
            query = Q(query & Q(date__lte=time_exit))
            query_hours = Q(query_hours & Q(days__date__lte=time_exit))
        # Указываем текущую дату, чтобы если события созданы на будущие числа, они не учитывались в статистике
        if not time_entry and not time_exit:
            query = Q(query & Q(date__lte=timezone.now().date()))
            query_hours = Q(query_hours & Q(days__date__lte=timezone.now().date()))

        qs = super().get_queryset().prefetch_related(
            Prefetch('days', queryset=Day.objects.filter(query).distinct()))

        qs_time_schedule = Sum('days__plan_working_hours', filter=query_hours)
        qs_time_work = Sum('days__real_working_hours', filter=query_hours)
        qs_real_overtime = Sum('days__real_overtime', filter=query_hours)
        qs_time_of_respectful_absence_fact = Sum('days__time_of_respectful_absence_fact', filter=query_hours)
        qs_time_of_not_respectful_absence_fact = Sum('days__time_of_not_respectful_absence_fact',
                                                     filter=query_hours)

        return qs.annotate(
            time_schedule=qs_time_schedule,  # Время работы по графику
            # Время уважительных прогулов (планируемое)
            time_work=qs_time_work,  # Время работы по факту
            real_overtime=qs_real_overtime,  # Время переработки по факту
            time_of_respectful_absence_fact=qs_time_of_respectful_absence_fact,
            time_of_not_respectful_absence_fact=qs_time_of_not_respectful_absence_fact
        )


class SerializerGetPercentMixin:

    def get_percent_time_work(self, obj):
        if not obj.time_work:
            return 0
        if not obj.time_schedule:
            return 0
        return float('{:.4}'.format(obj.time_work / obj.time_schedule * 100))

    def get_percent_time_of_respectful_absence(self, obj):
        if not obj.time_of_respectful_absence_fact:
            return 0
        if not obj.time_schedule:
            return 0
        return float('{:.4}'.format(obj.time_of_respectful_absence_fact / obj.time_schedule * 100))

    def get_percent_time_of_not_respectful_absence(self, obj):
        if not obj.time_of_not_respectful_absence_fact:
            return 0
        if not obj.time_schedule:
            return 0
        return float('{:.4}'.format(obj.time_of_not_respectful_absence_fact / obj.time_schedule * 100))
