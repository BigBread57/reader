from rest_framework import serializers
from rest_framework.fields import IntegerField

from accountBd.collections import UserRank, UserPosition
from accountBd.models import Profile, Project, User
from api.public.accountBd.mixins import SerializerGetPercentMixin
from api.public.readerBd.serializers import DayStatisticSerializer, ChoiceField


class UsersSerializer(serializers.ModelSerializer):
    """
    Класс, который отображает личную информацию о пользователях без статистики и информации о событиях
    """

    full_name = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    rank = ChoiceField(choices=UserRank.STATUS_CHOICES)
    position = ChoiceField(choices=UserPosition.STATUS_CHOICES)
    count_duty = IntegerField()

    class Meta:
        model = Profile
        fields = ('id', 'full_name', 'year_appeal', 'number_appeal', 'project', 'rank', 'position', 'count_duty')
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_project(self, obj):
        return f'{obj.project}'.strip()


class UsersCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Класс, который позволяет создавать и редактировать информацию о пользователе
    """

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'third_name', 'password', 'code')


class UsersStatisticSerializer(SerializerGetPercentMixin, serializers.ModelSerializer):
    """
    Класс позволяет получать полную статистику по всем пользователям, без информация по событиям.
    """

    full_name = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    time_schedule = serializers.DurationField(read_only=True)  # Время по графику (планируемое)
    time_work = serializers.DurationField(read_only=True)  # Время работы (фактическое)
    real_overtime = serializers.DurationField(read_only=True)  # Время сверх работы
    # Время уважительных прогулов (фактических)
    time_of_respectful_absence_fact = serializers.DurationField(read_only=True)
    # Время не уважительных прогулов (фактическое)
    time_of_not_respectful_absence_fact = serializers.DurationField(read_only=True)
    # Процентное отношение времени работы к общему времени
    percent_time_work = serializers.SerializerMethodField(read_only=True)
    # Процентное отношение уважительных прогулов к общему времени
    percent_time_of_respectful_absence = serializers.SerializerMethodField(read_only=True)
    # Процентное отношение не уважительных прогулов к общему времени
    percent_time_of_not_respectful_absence = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'full_name', 'year_appeal', 'number_appeal', 'project',
                  'time_schedule', 'time_work', 'real_overtime', 'time_of_respectful_absence_fact',
                  'time_of_not_respectful_absence_fact',
                  'percent_time_work', 'percent_time_of_respectful_absence', 'percent_time_of_not_respectful_absence')
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_project(self, obj):
        if not obj.project:
            return ''
        return f'{obj.project.name}'.strip()


class UserStatisticDetailSerializer(SerializerGetPercentMixin, serializers.ModelSerializer):
    """
    Класс отображает подробную информацию о пользователе с информацией о событиях, которые относятся к нему
    """

    full_name = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    events = DayStatisticSerializer(source='user.events', many=True, )  # Информация о событии
    time_work = serializers.DurationField(read_only=True)  # Время работы (фактическое)
    time_schedule = serializers.DurationField(read_only=True)  # Время работы по графику (планируемое)
    real_overtime = serializers.DurationField(read_only=True)  # Время переработки
    time_of_respectful_absence_fact = serializers.DurationField(read_only=True)  # Время уважительных прогулов
    time_of_not_respectful_absence_fact = serializers.DurationField(read_only=True)  # Время не уважительных прогулов
    # % фактической работы в общем количестве времени
    percent_time_work = serializers.SerializerMethodField(read_only=True)
    # % уважительных прогулов в общем количестве времени
    percent_time_of_respectful_absence = serializers.SerializerMethodField(read_only=True)
    # % не уважительных прогулов в общем количестве времени
    percent_time_of_not_respectful_absence = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'full_name', 'year_appeal', 'number_appeal', 'project', 'photo',
                  'user_id', 'time_work', 'time_schedule', 'real_overtime',
                  'time_of_respectful_absence_fact', 'time_of_not_respectful_absence_fact',
                  'percent_time_work', 'percent_time_of_respectful_absence', 'percent_time_of_not_respectful_absence',
                  'events')
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_project(self, obj):
        if not obj.project:
            return ''
        return f'{obj.project.name}'.strip()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Класс отображает инфоомрацию, которая доступна пользователю в его профиле
    """

    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    third_name = serializers.CharField(source='user.third_name')
    code = serializers.CharField(source='user.code')
    project = serializers.SerializerMethodField()
    rank = ChoiceField(choices=UserRank.STATUS_CHOICES)
    position = ChoiceField(choices=UserPosition.STATUS_CHOICES)
    count_duty = IntegerField()

    class Meta:
        model = Profile
        fields = ('id', 'first_name', 'last_name', 'third_name',
                  'code', 'year_appeal', 'number_appeal', 'project', 'rank', 'position', 'count_duty')

    def get_project(self, obj):
        return f'{obj.project}'.strip()


class ProjectsStatisticSerializer(SerializerGetPercentMixin, serializers.ModelSerializer):
    """
    Класс отображает статистическую инфомрацию по проектам
    """

    time_schedule = serializers.DurationField(read_only=True)  # Время по графику (планируемое)
    time_work = serializers.DurationField(read_only=True)  # Время работы (фактическое)
    real_overtime = serializers.DurationField(read_only=True)  # Время сверх работы
    # Время уважительных прогулов (фактических)
    time_of_respectful_absence_fact = serializers.DurationField(read_only=True)
    # Время не уважительных прогулов (фактическое)
    time_of_not_respectful_absence_fact = serializers.DurationField(read_only=True)
    # Процентное отношение времени работы к общему времени
    percent_time_work = serializers.SerializerMethodField(read_only=True)
    # Процентное отношение уважительных прогулов к общему времени
    percent_time_of_respectful_absence = serializers.SerializerMethodField(read_only=True)
    # Процентное отношение не уважительных прогулов к общему времени
    percent_time_of_not_respectful_absence = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name',
                  'time_schedule', 'time_work', 'real_overtime', 'time_of_respectful_absence_fact',
                  'time_of_not_respectful_absence_fact',
                  'percent_time_work', 'percent_time_of_respectful_absence', 'percent_time_of_not_respectful_absence')
        read_only_fields = fields


class ProjectsStatisticDetailSerializer(SerializerGetPercentMixin, serializers.ModelSerializer):
    """
    Класс отображает статистическую инфомрацию по проектам с событиями
    """

    events = DayStatisticSerializer(source='event_project', many=True)  # Информация о событии
    time_schedule = serializers.DurationField()  # Время по графику (планируемое)
    time_work = serializers.DurationField()  # Время работы (фактическое)
    real_overtime = serializers.DurationField()  # Время сверх работы
    # Время уважительных прогулов (фактических)
    time_of_respectful_absence_fact = serializers.DurationField()
    # Время не уважительных прогулов (фактическое)
    time_of_not_respectful_absence_fact = serializers.DurationField()
    # Процентное отношение времени работы к общему времени
    percent_time_work = serializers.SerializerMethodField()
    # Процентное отношение уважительных прогулов к общему времени
    percent_time_of_respectful_absence = serializers.SerializerMethodField()
    # Процентное отношение не уважительных прогулов к общему времени
    percent_time_of_not_respectful_absence = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'name',
                  'time_schedule', 'time_work', 'real_overtime', 'time_of_respectful_absence_fact',
                  'time_of_not_respectful_absence_fact',
                  'percent_time_work', 'percent_time_of_respectful_absence', 'percent_time_of_not_respectful_absence',
                  'events')
        read_only_fields = fields
