import datetime
import logging

from django.db import IntegrityError
from django.db.models import Max, Min
from django.utils import timezone
from rest_framework import viewsets, generics, status, exceptions
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response

from accountBd.collections import UserPosition, UserStatus
from accountBd.models import User, Profile, FileRepository
from docs.statistic_docx import event_statistic, journal
from readerBd.collections import Times, TypeOfDay
from readerBd.models import ControlTime, Day, ScheduleDuty, OrderOfDuty, ListEvents, Event
from .filters import ControlTimeFilter
from .permissions import IsPersonalOrReadOnly
from .serializers import ControlTimeReaderSerializer, DaySerializer, ControlTimeSerializer, EventSerializer, \
    ControlTimeScheduleDutySerializer, ListEventsSerializer, UpdateControlTimeSerializer, CreateUpdateDaySerializer
from .utils import overtime_calculation, change_appeal, calculation_time_variable

logging.basicConfig(level='INFO')


class ControlTimeViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет работать с информацией о времени входа/выхода по RFID-метке
    """

    permission_classes = (IsPersonalOrReadOnly,)
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
                                                                          time_exit__isnull=True).last()
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

            # Проверяем тип дня и высчитваем время переработки
            if day.type_of_day == TypeOfDay.WORK:
                control_time.overtime = overtime_calculation(control_time.time_entry,
                                                             control_time.time_exit, user, day)
            else:
                control_time.overtime = control_time.time_difference

            control_time.save()
            # Пересчитываем показатели дня, к которому относится control_time
            day = calculation_time_variable(day)
            day.save()

        # Если объект создается в первый раз, то ищется день, к которому относится control_time и сохраняется в БД
        # время входа, и приввязывается день к control_time
        else:
            try:
                day = Day.objects.get(user=user, date=timezone.now().date())
            except Day.DoesNotExist:
                raise exceptions.NotFound(detail={'message': 'Для фиксации времени необходимо создать текущий день.'})

            serializer.save(time_entry=timezone.now().replace(microsecond=0), day=day)

    def perform_update(self, serializer):
        # Перед изменением объекта control_time мы изменяем данные об этом control_time в объекте Day
        control_time = self.get_object()
        print(serializer.validated_data.get('time_exit'))

        if serializer.validated_data.get('time_exit').day() != control_time.time_exit.day() or \
                serializer.validated_data.get('time_entry').day() != control_time.time_entry.day():
            raise exceptions.ValidationError(detail={
                'message': f'Данная временная метка привязана к дате {control_time.time_exit.day()}. '
                           f'Укажите либо данную дату, либо выберите временную метку с интерисующей датой'})
        else:
            new_time_entry = serializer.validated_data.get('time_entry')
            new_time_exit = serializer.validated_data.get('time_exit')

        new_time_difference = new_time_exit - new_time_entry

        day = control_time.day
        user = get_object_or_404(User, id=day.user.id)

        # Пересчитываем время переработки с учетом новых показателей
        if day.type_of_day == TypeOfDay.WORK:
            new_overtime = overtime_calculation(new_time_entry, new_time_exit, user, day)
        else:
            new_overtime = new_time_difference

        serializer.save(time_difference=new_time_difference, overtime=new_overtime)

        # Пересчитываем показатели дня, к которому относится control_time
        day = calculation_time_variable(day)
        day.save()

    def perform_destroy(self, instance):
        # Перед удалением объекта control_time мы удаляем данные об этом control_time из объекта Day
        control_time = self.get_object()
        control_time.delete()

        # Пересчитываем показатели дня, к которому относится control_time
        day = calculation_time_variable(control_time.day)
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

    permission_classes = (IsPersonalOrReadOnly,)
    queryset = ControlTime.objects.all()
    serializer_class = ControlTimeSerializer

    def get_queryset(self):
        # Получаем все метки с текущей датой
        qs = super().get_queryset().filter(time_entry__date=timezone.now().date())
        # Берем пользователей, к которым относятся control_time, получаем максимальное время входа данных пользователей,
        # то есть самые последнии метки.
        return qs.filter(
            time_entry__in=qs.values('day__user').annotate(time_entry=Max('time_entry')).values('time_entry')).order_by(
            'time_exit')


class ListEventsViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет работать со списком событий, который могут случиться (разгрузка белья, помощь КР и т.д.)
    """

    permission_classes = (IsPersonalOrReadOnly,)
    queryset = ListEvents.objects.all()
    serializer_class = ListEventsSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет работать с событиями, детализировать их и добавлять к объекту Day
    """

    permission_classes = (IsPersonalOrReadOnly,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class DayViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет отображать информацию о днях
    """

    permission_classes = (IsPersonalOrReadOnly,)
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

        # Автоматически устанавливаем поля plan_working_hours в зависимости от типа дня и пользователя
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
        # Переменная чтобы запомнить текущее значение реального рабочего времени
        real_working_hours_save = day.real_working_hours

        # Ниже просто проверяется изменен ли тип дня, и проводится перерасчет показателей
        if day.type_of_day == TypeOfDay.WORK:
            if serializer.validated_data.get('type_of_day') != TypeOfDay.WORK:
                day.real_working_hours = datetime.timedelta(0)
                day.real_overtime += real_working_hours_save
        else:
            if serializer.validated_data.get('type_of_day') == TypeOfDay.WORK:
                day.type_of_day = TypeOfDay.WORK
                day = calculation_time_variable(day)

        day.save()
        serializer.save()

    def get_serializer_class(self):
        return self.action_to_serializers.get(
            self.action,
            self.serializer_class
        )

    @action(detail=False)
    def journal(self, request, *args, **kwargs):
        """
        Функия необходима для формирования журнала дежурств, тот который ТБ в лаборатории

        :return: Файл для скачивания журнала дежурств
        """

        # Список для всех пользователй, которые пришли в лабораторию
        list_user = []
        # ПОлучам дни рабочих дней оператора на текущую дату
        days = Day.objects.filter(user__profile__position__in=(UserPosition.OPERATOR, UserPosition.SENIOR_OPERATOR),
                                  date=timezone.now().date(),
                                  type_of_day=TypeOfDay.WORK)
        # Функция для создания макета документа
        document_name = f'visit_log-{timezone.now().strftime("%Y-%m-%d")}.docx'
        journal(document_name)

        # Формируем список операторов, которые пришли в лабораторию
        for day in days:
            user = day.user
            # Функция для добавления в ранее созданный документ инфомрации о пользователях
            list_user.append([timezone.now().date().strftime("%Y-%m-%d"),
                              user.profile.get_rank_display(),
                              user.profile.get_position_display(),
                              user.get_full_name()])
        event_statistic(list_user, document_name)

        # Добавляет в бд инфомрацию о сформированном файле
        file_repository, _ = FileRepository.objects.get_or_create(
            name=document_name,
            defaults={'file': f'docs/{document_name}'})

        return Response({'url': file_repository.file.url})


class ScheduleDutyViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет работать с информацией о расписании дежурств по лаборатории и автоматически формировать его
    """

    permission_classes = (IsPersonalOrReadOnly,)
    queryset = ScheduleDuty.objects.all()
    serializer_class = ControlTimeScheduleDutySerializer

    action_to_serializers = {
        'auto': ControlTimeScheduleDutySerializer,
    }

    @action(detail=False)
    def auto(self, request, *args, **kwargs):
        """
        Функция автоматически формирует спсиок дежурных по лаборатории

        :return: Автоматически сформированный список дежурств по лаборатории
        """

        # Переменная для запоминания id тех, кто уже подежурил.
        remember_count_duty = []
        # Переменная для создания конечного графика.
        schedule_list = []
        # Получаем очередь дежурства.
        try:
            priority_duty = OrderOfDuty.load()
        except IntegrityError:
            raise exceptions.NotFound(detail={'message': 'Для автоматического формирования расписания необходимо '
                                                         'указать дежурный призыв и в профиле пользователей указать '
                                                         'номер и год призыва. Для указания дежурного призыва '
                                                         'обратитесь к администратуру.'})

        number_appeal = priority_duty.number_appeal

        # Создаем график на количество пользователей.
        for days_week in range(0, len(User.objects.all())):

            # Получаем дату, с учетом итерации цикла.
            date_days_week = timezone.now().date() + datetime.timedelta(days=days_week)

            # Если в графике уже есть запись на дату, которая попала в цикл, то пропускаем данную дату
            if ScheduleDuty.objects.filter(date=date_days_week).first():
                continue

            # Если выходной день пропускаем
            elif date_days_week.weekday() in (5, 6):
                continue

            else:
                qs_profile = Profile.objects.filter(number_appeal=number_appeal).exclude(
                    status=UserStatus.DEMOB).order_by('user__last_name')
                # Узнаем максимальное и минимальное количество нарядов у операторов дежурного призыва.
                max_count_duty = qs_profile.aggregate(max=Max('count_duty'))['max']
                min_count_duty = qs_profile.aggregate(min=Min('count_duty'))['min']

                # Получаем всех пользователей, которые не входят в список тех, кто уже подежурил
                users_yes_duty = list(qs_profile.exclude(user_id__in=set(remember_count_duty)).values('user_id'))

                # Получаем всех пользователей на текущую дату, кто не может дежурить (госпиталь, командировка и другое)
                users_not_duty = list(qs_profile.filter(user__days__date=date_days_week).exclude(
                    user__days__type_of_day=TypeOfDay.WORK).values('user_id').distinct())

                # Проверяем совпадает ли список тех кто не дежурил с теми кто не может дежурить или с пустым списком
                # (то есть все дежурили) если совпадает, то меняем приоритет призыва для дежурства.

                if users_yes_duty in (users_not_duty, []):
                    # Вызываем функцию, которая изменяет приоритет дежурства
                    change_appeal(priority_duty)
                    # Сохраняем приоритет, обновляем переменную, которая отвечает за информацию о призыве,
                    # обновляем переменную, отвечающую за запоминание id тех, кто уже подежурил
                    priority_duty.save()
                    number_appeal = priority_duty.number_appeal
                    remember_count_duty = []
                    # Снова формируем запрос на профили новых пользователей
                    qs_profile = Profile.objects.filter(number_appeal=number_appeal).exclude(
                        status=UserStatus.DEMOB).order_by('user__last_name')

                # Проверяем у всех ли в призыве равное количество нарядов и в списке дежурств пусто.
                # Если равно и пусто, то мы берем первого пользователя, который присуствует в лаборатории,
                # предварительно отсортировав по алфавиту.
                if max_count_duty == min_count_duty:

                    if not remember_count_duty:
                        # Получаем профиль первого пользователя
                        profile_user = qs_profile.first()

                        schedule_list.append(ScheduleDuty(
                            user_id=profile_user.user.id,
                            date=date_days_week,
                        ))
                        # Изменяем количество нарядов в профиле пользователя
                        profile_user.count_duty += 1
                        profile_user.save()
                        # Формируем список подежуривших пользователей
                        remember_count_duty.append(profile_user.user.id)

                    # Если количество нарядов равное список дежурств не пустой, то изменяем приоритет дежурства
                    # Проверка количества отдежуривших с списке remember_count_duty необходима для того,
                    # чтобы не получилось так, что у 1 человека нарядов меньше чем у остальных, он 1 раз отдежурит и
                    # приоритет дежурства поменяется. Это условие сделет так, что он подежурит и его призыв также
                    # дальше пойдет дежурить

                    elif remember_count_duty and len(remember_count_duty) > 2:
                        change_appeal(priority_duty)
                        # Сохраняем приоритет, обновляем переменную, которая отвечает за информацию о призыву,
                        # обновляем переменную, отвечающую за запоминание id тех, кто уже подежурил
                        priority_duty.save()
                        number_appeal = priority_duty.number_appeal
                        remember_count_duty = []

                # Если количество нарядов не равное
                elif max_count_duty != min_count_duty:
                    # Ищем пользователя, у котороторого количетсво нарядов минимально
                    profile_user = qs_profile.filter(count_duty=min_count_duty).first()

                    schedule_list.append(ScheduleDuty(
                        user_id=profile_user.user_id,
                        date=date_days_week,
                    ))

                    profile_user.count_duty += 1
                    profile_user.save()
                    # Формируем список подежуривших пользователей
                    remember_count_duty.append(profile_user.user_id)

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
