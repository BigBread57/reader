from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

from accountBd.collections import UserRank, UserPosition, NumberAppeal, UserStatus


class User(AbstractUser):
    """
    К default классу user добавляется отчество пользователя и code, который привязан к часам оператора, или
    другим средства, которые содержат магнитную метку и идентефицируют пользователя.
    """

    third_name = models.CharField('Отчество', max_length=150, unique=False, blank=True)
    code = models.CharField('Код', max_length=30, unique=True)

    def get_full_name(self):
        full_name = '%s %s %s' % (self.last_name, self.first_name, self.third_name)
        return full_name.strip()

    def save(self, *args, **kwargs):
        if not self.id:
            super().save(*args, **kwargs)
            Profile.objects.create(user=self)
        else:
            super().save(*args, **kwargs)


class Project(models.Model):
    """
    Класс содержит информацию о названии проекта, за которым закреплен оператор или персонал
    """

    name = models.CharField('Шифр проекта', max_length=50)

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

    def __str__(self):
        return self.name


class Profile(models.Model):
    """
    Класс содержит инфомрацию о прифиле пользователя.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    year_appeal = models.SmallIntegerField('Год призыва', null=True, blank=True)
    number_appeal = models.SmallIntegerField('Номер призыва', choices=NumberAppeal.CHOICES, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.RESTRICT, related_name='profiles', verbose_name='Проект',
                                null=True, blank=True)
    rank = models.CharField('Звание', max_length=20, choices=UserRank.STATUS_CHOICES,
                            default=UserRank.PRIVATE, blank=True, null=True)
    position = models.CharField('Должность', max_length=20, choices=UserPosition.STATUS_CHOICES,
                                default=UserPosition.OPERATOR)
    count_duty = models.IntegerField('Количество нарядов', default=0)
    status = models.CharField('Статус пользователя', max_length=20, choices=UserStatus.STATUS_CHOICES,
                              default=UserStatus.ARMY_SERVICE)
    photo = models.ImageField('Фотография', upload_to='users', blank=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профиля'

    def __str__(self):
        return 'Профиль пользователя {}'.format(self.user)


class FileRepository(models.Model):
    """Класс для хранения файлов"""

    name = models.CharField('Название файла', max_length=150, unique=True)
    file = models.FileField('Файл', upload_to='docs')

    class Meta:
        verbose_name = 'Хранилище'
        verbose_name_plural = 'Хранилище'

    def __str__(self):
        return f'{self.file.url}'
