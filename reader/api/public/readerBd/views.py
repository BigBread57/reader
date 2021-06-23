import datetime
import logging

from django.db.models import Max, Min
from django.utils import timezone
from rest_framework import viewsets, generics, status, exceptions
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accountBd.collections import UserPosition
from accountBd.models import User, Profile, FileRepository
from docs.statistic_docx import event_statistic, journal
from readerBd.collections import Times, TypeOfDay
from readerBd.models import ControlTime, Day, ScheduleDuty, OrderOfDuty, ListEvents, Event
from .filters import ControlTimeFilter
from .serializers import ControlTimeReaderSerializer, DaySerializer, ControlTimeSerializer, EventSerializer, \
    ControlTimeScheduleDutySerializer, ListEventsSerializer, UpdateControlTimeSerializer, CreateUpdateDaySerializer
from .utils import overtime_calculation, change_appeal, calculation_absence

logging.basicConfig(level='INFO')


class ControlTimeViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет работать с информацией о времени входа/выхода по RFID-метке
    """

    permission_classes = (AllowAny,)
    queryset = ControlTime.objects.all().order_by('-time_entry')
    serializer_class = ControlTimeReaderSerializer
    filter_class = ControlTimeFilter

    action_to_serializers = {
        'list': ControlTimeSerializer,
        'retrieve': ControlTimeSerializer,
        'update': UpdateControlTimeSerializer
    }

    def perform_create(self, serializer):
        # Проверяем, создается ли объект с кодом впервые или нет. Если в первый раз,
        # то ищем пользователя которому принадлежит код, иначе возвращаем предупреждение, что код не найден и код 200
        # чтобы программа по принятию RFID-меток не выдавала ошибку и не останавливала работу считывателя
        control_time = ControlTime.objects.order_by('-time_entry').filter(code=serializer.validated_data.get('code'),
                                                                          time_exit=None).last()
        try:
            user = User.objects.get(code=serializer.validated_data.get('code'))
        except User.DoesNotExist:
            return Response(status=status.HTTP_200_OK, data={
                'message': 'Вы ввели RFID код, который не зарегистрирован в системе. '
                           'Создайте пользователя и установите ему используемый RFID код'})

        # Если объект уже был создан, то есть пользователь уже заходил в лабораторию, то записывается время выхода,
        # считается разница между временем входа и выхода и ищется событие, к которому относится анализируемая
        # временная метка
        if control_time:
            control_time.time_exit = timezone.now().replace(microsecond=0)
            control_time.time_difference = control_time.time_exit - control_time.time_entry
            day = Day.objects.get(id=control_time.day.id)

            # Проверяем тип дня. Если рабочий, то в рабочее время записываем (time_difference - overtime),
            # а переработку (overtime) считаем в функции
            if day.type_of_day == TypeOfDay.WORK:
                control_time.overtime = overtime_calculation(control_time.time_entry,
                                                             control_time.time_exit, user, day)
                day.real_overtime += control_time.overtime
                day.real_working_hours += control_time.time_difference - control_time.overtime

            # Если день не рабочий, например наряд или госпиталь или отпуск, то мы в рабочее время заносим 0,
            # а в переработку time_difference, потому что пользователь не должен быть на рабочем месте
            else:
                day.real_working_hours = datetime.timedelta(0)
                control_time.overtime = control_time.time_difference
                day.real_overtime += control_time.overtime

            control_time.save()
            day = calculation_absence(day)
            day.save()

        else:
            try:
                day = Day.objects.get(user=user, date=timezone.now().date())
            except Day.DoesNotExist:
                raise exceptions.NotFound(detail={'message': 'Для фиксации времени необходимо создать текущий день.'})

            serializer.save(time_entry=timezone.now().replace(microsecond=0), day=day)

    def perform_update(self, serializer):
        # Перед изменением объекта control_time мы изменяем данные об этом control_time в объекте Day

        control_time = self.get_object()
        new_time_difference = serializer.validated_data.get('time_exit') - serializer.validated_data.get('time_entry')
        day = get_object_or_404(Day, date=serializer.validated_data.get('time_entry').date())
        user = get_object_or_404(User, id=day.user.id)

        if day.type_of_day == TypeOfDay.WORK:

            new_overtime = overtime_calculation(serializer.validated_data.get('time_entry'),
                                                serializer.validated_data.get('time_exit'), user, day)
            day.real_overtime += new_overtime - control_time.overtime
            day.real_working_hours += new_time_difference - new_overtime - \
                                      control_time.time_difference - control_time.overtime

        else:
            new_overtime = new_time_difference
            day.real_overtime += new_overtime - control_time.overtime

        day = calculation_absence(day)
        day.save()
        serializer.save(time_difference=new_time_difference, overtime=new_overtime)

    def perform_destroy(self, instance):
        # Перед удалением объекта control_time мы удаляем данные об этом control_time из объекта Day

        control_time = self.get_object()
        day = get_object_or_404(Day, id=control_time.day.id)

        if control_time.overtime > datetime.timedelta(0) and control_time.time_difference == datetime.timedelta(0):
            day.real_overtime -= control_time.overtime

        if control_time.overtime > datetime.timedelta(0) and control_time.time_difference > datetime.timedelta(0):
            day.real_working_hours -= control_time.time_difference - control_time.overtime
            day.real_overtime -= control_time.overtime

        if control_time.overtime == datetime.timedelta(0) and control_time.time_difference > datetime.timedelta(0):
            day.real_working_hours -= control_time.time_difference

        control_time.delete()
        day = calculation_absence(day)
        day.save()

    def get_serializer_class(self):
        return self.action_to_serializers.get(
            self.action,
            self.serializer_class
        )


class ControlTimeTodayList(generics.ListAPIView):
    """
    Класс позволяет работать с информацией о времени входа и выхода на текущую дату.
    """

    permission_classes = (AllowAny,)
    queryset = ControlTime.objects.all()
    serializer_class = ControlTimeSerializer

    def get_queryset(self):
        qs = super().get_queryset().filter(time_entry__date=timezone.now().date())
        return qs.filter(
            time_entry__in=qs.values('day__user').annotate(time_entry=Max('time_entry')).values('time_entry')).order_by(
            'time_exit')


class ListEventsViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет работать со списком событий, который могут случиться (разгрузка белья, помощь КР и т.д.)
    """

    permission_classes = (AllowAny,)
    queryset = ListEvents.objects.all()
    serializer_class = ListEventsSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет работать с событиями, детализировать их и добавлять к объекту Day
    """

    permission_classes = (AllowAny,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class DayViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет отображать информацию о днях
    """

    permission_classes = (AllowAny,)
    queryset = Day.objects.all().order_by('-date',)
    serializer_class = DaySerializer
    filterset_fields = ('user', 'date', 'type_of_day')
    action_to_serializers = {
        'create': CreateUpdateDaySerializer,
        'update': CreateUpdateDaySerializer,
        'journal': DaySerializer,
    }

    def perform_create(self, serializer):
        # Устанавливаем проект, который указан в профиле пользователя, если не указан в форме
        if serializer.validated_data.get('project'):
            user_project = serializer.validated_data.get('project')
        else:
            user_project = Profile.objects.get(user_id=serializer.validated_data.get('user')).project

        # Автоматически устанавливаем поля plan_working_hours и time_of_respectful_absence_plan в зависимости
        # от типа дня и пользователя

        if serializer.validated_data.get('user').profile.position in (UserPosition.OPERATOR,
                                                                      UserPosition.SENIOR_OPERATOR):
            plan_working_hours = Times.TIME_WORK_OPERATOR
        else:
            plan_working_hours = Times.TIME_WORK_PERSONAL

        if serializer.validated_data.get('type_of_day') in (TypeOfDay.DUTY, TypeOfDay.HOSPITAL,
                                                            TypeOfDay.BUSINESS_TRIP, TypeOfDay.OUTPUT):
            serializer.save(plan_working_hours=datetime.timedelta(0),
                            project=user_project)

        elif serializer.validated_data.get('type_of_day') == TypeOfDay.WORK:
            serializer.save(plan_working_hours=plan_working_hours,
                            project=user_project)

    # Функция необходима для проверки, создан ли день на указанную дату или нет.
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        day = Day.objects.filter(user_id=serializer.validated_data.get('user'),
                                 date=serializer.validated_data.get('date')).first()
        if day:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'message': 'День на указанную дату уже создан. Удалите его или отредактируйте'})
        else:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        day = self.get_object()
        profile_user = get_object_or_404(Profile, user=day.user.id)
        # Переменные чтобы запомнить значения
        real_working_hours_save = day.real_working_hours

        if day.type_of_day == TypeOfDay.WORK:
            if serializer.validated_data.get('type_of_day') != TypeOfDay.WORK:
                day.real_working_hours = datetime.timedelta(0)
                day.real_overtime += real_working_hours_save
        elif day.type_of_day != TypeOfDay.WORK:
            if serializer.validated_data.get('type_of_day') == TypeOfDay.WORK:

                if profile_user.position in (UserPosition.OPERATOR, UserPosition.SENIOR_OPERATOR):
                    # Проверяем количество часов, которые оператор отработал.
                    if day.real_overtime > Times.TIME_WORK_OPERATOR:
                        day.real_working_hours = Times.TIME_WORK_OPERATOR
                        day.real_overtime -= day.real_working_hours
                    else:
                        day.real_working_hours = day.real_overtime
                        day.real_overtime = datetime.timedelta(0)
                else:
                    if day.real_overtime > Times.TIME_WORK_PERSONAL:
                        day.real_working_hours = Times.TIME_WORK_PERSONAL
                        day.real_overtime -= day.real_working_hours
                    else:
                        day.real_working_hours = day.real_overtime
                        day.real_overtime = datetime.timedelta(0)
        day.save()
        serializer.save()

    def get_serializer_class(self):
        return self.action_to_serializers.get(
            self.action,
            self.serializer_class
        )

    @action(detail=False)
    def journal(self, request, *args, **kwargs):
        list_user = []
        days = Day.objects.filter(user__profile__position__in=(UserPosition.OPERATOR, UserPosition.SENIOR_OPERATOR),
                                  date=timezone.now().date(),
                                  type_of_day=TypeOfDay.WORK)
        # Функция для создания макета документа
        document_name = f'visit_log-{timezone.now().strftime("%Y-%m-%d")}.docx'
        journal(document_name)

        for day in range(0, len(days)):
            user = days[day].user
            # Функция для добавления в ранее созданный документ инфомрации о пользователях
            list_user.append([timezone.now().date().strftime("%Y-%m-%d"),
                              user.profile.get_rank_display(),
                              user.profile.get_position_display(),
                              user.get_full_name()])
        event_statistic(list_user, document_name)

        file_repository, _ = FileRepository.objects.get_or_create(
            name=document_name,
            defaults={'file': f'docs/{document_name}'})

        return Response({'url': file_repository.file.url})


class ScheduleDutyViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет работать с информацией о расписании дежурств по лаборатории
    """

    permission_classes = (AllowAny,)
    queryset = ScheduleDuty.objects.all()
    serializer_class = ControlTimeScheduleDutySerializer

    action_to_serializers = {
        'auto': ControlTimeScheduleDutySerializer,
    }

    @action(detail=False)
    def auto(self, request, *args, **kwargs):
        # Переменная для запоминания id тех, кто уже подежурил.
        remember_count_duty = []
        # Переменная для создания конечного графика.
        schedule_list = []
        # Получаем очередь дежурства.
        priority_duty = OrderOfDuty.load()
        number_appeal = priority_duty.number_appeal
        # Создаем график на количество пользователей.
        for days_week in range(0, len(User.objects.all())):
            # Получаем дату, с учетом итерации цикла.
            date_days_week = timezone.now().date() + datetime.timedelta(days=days_week)
            # Если дня нет, заканчиваем цикл
            if Day.objects.filter(date=date_days_week).first() is None:
                break
            # Если в графике уже есть запись на дату, которая попала в цикл, то пропускаем данную дату
            elif ScheduleDuty.objects.filter(date=date_days_week).first():
                continue
            # Если выходной день пропускаем
            elif Day.objects.filter(date=date_days_week).first().type_of_day == TypeOfDay.OUTPUT:
                continue
            else:
                # Узнаем максимальное и минимальное количество нарядов у операторов дежурного призыва.
                max_count_duty = Profile.objects.filter(
                    number_appeal=number_appeal).aggregate(max=Max('count_duty'))['max']
                min_count_duty = Profile.objects.filter(
                    number_appeal=number_appeal).aggregate(min=Min('count_duty'))['min']

                # Получаем всех пользователей, которые не входят в список тех, кто уже подежурил
                users_yes_duty = Profile.objects.filter(
                    number_appeal=number_appeal).exclude(
                    user_id__in=set(remember_count_duty)).values('user_id')

                # Получаем всех пользователей на текущую дату, кто не может дежурить (госпиталь, командировка и другое)
                users_not_duty = Profile.objects.filter(
                    number_appeal=number_appeal,
                    user__days__date=date_days_week).exclude(
                    user__days__type_of_day=TypeOfDay.WORK).values('user_id').distinct()

                # Проверяем совпадает ли список не дежуривших и тех, кто не может дежурить
                # если совпадает, то меняем приоритет призыва для дежурства

                if (list(users_yes_duty)) in ((list(users_not_duty)), []):
                    # Вызываем фуннкцию, которая изменяет приоритет дежурства
                    change_appeal(priority_duty)
                    # Сохраняем приоритет, обновляем переменную, которая отвечает за информацию о призыву,
                    # обновляем переменную, отвечающую за запоминание id тех, кто уже подежурил
                    priority_duty.save()
                    number_appeal = priority_duty.number_appeal
                    remember_count_duty = []

                # Получение id пользователей исходя из призыва.
                users_id = Profile.objects.filter(number_appeal=number_appeal).order_by(
                    'user__last_name').values(
                    'user')

                # Проверяем у всех ли в призыве равное количество нарядов. Если равно, то мы берем первого пользователя
                # который присуствует в лаборатории, предварительно отсортировав по алфавиту.
                if max_count_duty == min_count_duty:
                    if not remember_count_duty:
                        day = Day.objects.filter(user_id__in=users_id, date=date_days_week,
                                                 type_of_day=TypeOfDay.WORK).order_by('user__last_name').first()
                        if not day:
                            raise exceptions.NotFound(detail={'message': 'День не найден. Создайте день.'})
                        else:
                            schedule_list.append(ScheduleDuty(
                                user_id=day.user_id,
                                date=date_days_week,
                            ))
                            # Изменяем количество нарядов в профиле пользователя
                            profile_user = Profile.objects.filter(user_id=day.user_id).first()
                            profile_user.count_duty += 1
                            profile_user.save()

                        remember_count_duty.append(users_id.first()['user'])
                    else:
                        # Вызываем фуннкцию, которая изменяет приоритет дежурства
                        change_appeal(priority_duty)
                        # Сохраняем приоритет, обновляем переменную, которая отвечает за информацию о призыву,
                        # обновляем переменную, отвечающую за запоминание id тех, кто уже подежурил
                        priority_duty.save()
                        number_appeal = priority_duty.number_appeal
                        remember_count_duty = []

                elif max_count_duty != min_count_duty:
                    # Ищем день пользователя, у котороторого количетсво нарядов минимально
                    day = Day.objects.filter(
                        date=date_days_week,
                        type_of_day=TypeOfDay.WORK,
                        user_id=Profile.objects.filter(
                            count_duty=min_count_duty, number_appeal=number_appeal).order_by(
                            'user__last_name').values('user').first()['user']
                    ).first()

                    if not day:
                        raise exceptions.NotFound(detail={'message': 'День не найден. Создайте день.'})
                    else:
                        schedule_list.append(ScheduleDuty(
                            user_id=day.user_id,
                            date=date_days_week,
                        ))
                        profile_user = Profile.objects.filter(user_id=day.user_id).first()
                        profile_user.count_duty += 1
                        profile_user.save()

                    remember_count_duty.append(day.user_id)

        ScheduleDuty.objects.bulk_create(schedule_list)
        serializer = self.get_serializer(ScheduleDuty.objects.all(), many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        schedule_duty = ScheduleDuty.objects.filter(date=serializer.validated_data.get('date')).first()
        if schedule_duty:
            profile_user = Profile.objects.filter(user_id=schedule_duty.user.id).first()
            profile_user.count_duty += 1
            profile_user.save()
        serializer.save()

    def perform_update(self, serializer):
        schedule_duty = ScheduleDuty.objects.filter(date=serializer.validated_data.get('date')).first()
        if schedule_duty:
            profile_old_user = Profile.objects.filter(user_id=schedule_duty.user.id).first()
            profile_old_user.count_duty -= 1
            profile_old_user.save()

            profile_new_user = Profile.objects.filter(user_id=serializer.validated_data.get('user')).first()
            profile_new_user.count_duty += 1
            profile_new_user.save()

        serializer.save()
