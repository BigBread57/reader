from rest_framework import serializers

from readerBd.collections import TypeOfDay
from readerBd.models import ControlTime, Day, ScheduleDuty, ListEvents, Event


class ChoiceField(serializers.ChoiceField):
    """
    Класс необходим для отображение человеко-читаемых значений choices в сериализаторах
    """

    def to_representation(self, obj):
        if obj == '' and self.allow_blank:
            return obj
        return self._choices[obj]


class ControlTimeReaderSerializer(serializers.ModelSerializer):
    """
    Класс позволяет фиксировать RFID-метки
    """

    class Meta:
        model = ControlTime
        fields = ('id', 'code')


class EventSerializer(serializers.ModelSerializer):
    """
    Класс позволяет работать с событиями, детализировать их и добавлять к объекту Day
    """

    class Meta:
        model = Event
        fields = ('id', 'type_event', 'time_plan', 'respectful_absence', 'comment')
        read_only_fields = ('id', )


class ListEventsSerializer(serializers.ModelSerializer):
    """
    Класс позволяет работать со списком событий, который могут случиться (разгрузка белья, помощь КР и т.д.)
    """

    class Meta:
        model = ListEvents
        fields = ('id', 'name')


class ControlTimeSerializer(serializers.ModelSerializer):
    """
     Класс позволяет получать информацию о времени входа и выхода.
    """

    id_user = serializers.IntegerField(source='day.user.id')
    time_entry = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    time_exit = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = ControlTime
        fields = ('id', 'id_user', 'full_name', 'time_entry', 'time_exit', 'time_difference', 'overtime')
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.day.user.get_full_name()


class UpdateControlTimeSerializer(serializers.ModelSerializer):
    """
    Класс позволяет осуществлять редактирование control_time
    """

    time_entry = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    time_exit = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ControlTime
        fields = ('id', 'time_entry', 'time_exit')


class DaySerializer(serializers.ModelSerializer):
    """
    Класс позволяет отображать информацию о событиях
    """

    full_name = serializers.SerializerMethodField()
    type_of_day = ChoiceField(choices=TypeOfDay.STATUS_CHOICES)
    event = EventSerializer(many=True)
    project = serializers.SerializerMethodField()

    class Meta:
        model = Day
        fields = ('id', 'user', 'full_name', 'project', 'date', 'type_of_day', 'event',
                  'plan_working_hours', 'real_working_hours', 'time_of_respectful_absence_fact',
                  'time_of_not_respectful_absence_fact', 'real_overtime')
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_project(self, obj):
        return f'{obj.project}'.strip()


class CreateUpdateDaySerializer(serializers.ModelSerializer):

    type_of_day = ChoiceField(choices=TypeOfDay.STATUS_CHOICES)

    class Meta:
        model = Day
        fields = (
            'id', 'user', 'project', 'date', 'type_of_day',
            'event', 'plan_working_hours')
        read_only_fields = ('id', )


class DayStatisticSerializer(serializers.ModelSerializer):
    """
    Класс необходим для предоставления информации о дне и используется в других сериализаторах
    UserStatisticDetailSerializer и ProjectsStatisticDetailSerializer
    """

    control_events = ControlTimeSerializer(many=True)
    type_of_day = ChoiceField(choices=TypeOfDay.STATUS_CHOICES)
    event = EventSerializer()
    project = serializers.SerializerMethodField()

    class Meta:
        model = Day
        fields = (
            'id', 'user', 'date', 'project', 'type_of_day',
            'control_events', 'event', 'plan_working_hours', 'real_working_hours',
            'time_of_respectful_absence_fact', 'time_of_not_respectful_absence_fact', 'real_overtime')

    def get_project(self, obj):
        return f'{obj.project}'.strip()


class ControlTimeScheduleDutySerializer(serializers.ModelSerializer):
    """
    Класс позволяет работать с информацией о расписании дежурств по лаборатории
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleDuty
        fields = ('id', 'user', 'full_name', 'date')

    def get_full_name(self, obj):
        return obj.user.get_full_name()
