from datetime import timedelta

from django.conf import settings
from django.db import models

from accountBd.models import Project
from readerBd.collections import TypeOfDay, Times
from ws.utils import send_event


class ListEvents(models.Model):
    """
    Класс прдназначен для создания событий, которые могут произойти в рабочий день.
    Для операторов данные события могут быть представлены посещением конференций, помощью
    в расположении роты, разного рода срочными делами, которые не относятся к научной деятельности,
    но выполняются во время нее
    """

    name = models.CharField('Название события', max_length=50, unique=True)

    class Meta:
        verbose_name = 'Название события'
        verbose_name_plural = 'Список названий событий'

    def __str__(self):
        return self.name


class Event(models.Model):
    """
    Класс позволяет работать с событиями, детализировать их и добавлять к объекту Day
    """

    type_event = models.ForeignKey(ListEvents, on_delete=models.CASCADE, related_name='events',
                                   verbose_name='Тип события', blank=True, null=True)
    time_plan = models.DurationField('Планируемое количество времени на событие', default=timedelta(0))
    respectful_absence = models.BooleanField('Уважительное событие', default=True)
    comment = models.TextField('Комментарий к событию', blank=True, null=True)

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    def __str__(self):
        return self.type_event.name


class Day(models.Model):
    """
    Класс предназначен для хранения информации об одном дне. Также данный класс в себе содержит акумулирующую
    информацию о рабочем времени и времени сверхурочной работы, об уважительном  не уважительном отсутствии.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='days')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='days',
                                null=True, blank=True, db_index=True)
    date = models.DateField('Дата события', db_index=True)
    type_of_day = models.CharField('Тип дня', max_length=20, choices=TypeOfDay.STATUS_CHOICES,
                                   default=TypeOfDay.WORK)
    event = models.ManyToManyField(Event, related_name='days', verbose_name='Событие', blank=True)
    plan_working_hours = models.DurationField('Запланированное количество часов для работы', blank=True, null=True,
                                              default=Times.TIME_WORK_OPERATOR)
    real_working_hours = models.DurationField('Количество фактически отработанного времени',
                                              blank=True, default=timedelta(0))
    time_of_respectful_absence_fact = models.DurationField('Время уважительного отсутствия ',
                                                           blank=True, default=timedelta(0))
    time_of_not_respectful_absence_fact = models.DurationField('Время не уважительных прогулов (фактическое)',
                                                               blank=True, default=timedelta(0))
    real_overtime = models.DurationField('Количество переработанного времени',
                                         blank=True, default=timedelta(0))

    class Meta:
        verbose_name = 'День'
        verbose_name_plural = 'Дни'

    def __str__(self):
        return f'{self.user} {self.date}'


class ControlTime(models.Model):
    """
    Класс предназначен для хранения информации о RFID-метках, а также о разнице времени между временем входа
    и выхода и о времени переработки.
    """

    day = models.ForeignKey(Day, on_delete=models.CASCADE, verbose_name='День', related_name='control_times')
    code = models.CharField('Код', max_length=150)
    time_entry = models.DateTimeField('Время входа')  # Время входа в лабораторию
    time_exit = models.DateTimeField('Время выхода', null=True, blank=True)  # Время выхода из лаборатории
    time_difference = models.DurationField('Время присутствия', null=True,
                                           blank=True)  # Разница между входом и выходом в лабораторию
    overtime = models.DurationField('Время переработки', null=True,
                                    blank=True, default=timedelta(0))  # Время переработки

    class Meta:
        verbose_name = 'Код'
        verbose_name_plural = 'Коды'

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # функция необходима для работы websocket
        send_event(message='update')


class ScheduleDuty(models.Model):
    """
    Класс предназначен для храенения информации о графике дежурств.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField('Дата дежурсвта')

    class Meta:
        verbose_name = 'Расписание дежурств'
        verbose_name_plural = 'Расписание дежурств'

    def __str__(self):
        return self.user


class OrderOfDuty(models.Model):
    """
    Синглтон, который содержит инфомрациюю о призыве, который должен дежурить по расписанию
    """

    year_appeal = models.SmallIntegerField('Год призыва')
    number_appeal = models.SmallIntegerField('Номер призыва')

    def save(self, *args, **kwargs):
        self.pk = 1
        super(OrderOfDuty, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name = 'Очередь призыва в дежурствах'
        verbose_name_plural = 'Очередь призыва в дежурствах'
