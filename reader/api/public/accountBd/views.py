from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accountBd.collections import UserPosition
from docs.statistic_docx import users_statistic_report, user_statistic_report
from .filters import UserStatisticFilter, ProjectStatisticFilter
from .mixins import StatisticUserMixin, StatisticProjectMixin
from .serializers import UsersStatisticSerializer, UserStatisticDetailSerializer, ProfileSerializer, UsersSerializer, \
    ProjectsStatisticSerializer, ProjectsStatisticDetailSerializer, UsersCreateUpdateSerializer
from accountBd.models import Profile, Project, FileRepository


class UsersViewSet(viewsets.ModelViewSet):
    """
    Класс позволяет отображать справочную информацию о пользователе/пользователях
    без статистики и информации о событиях.
    """

    permission_classes = (AllowAny,)
    queryset = Profile.objects.all()
    serializer_class = UsersSerializer
    filterset_fields = ('year_appeal', 'number_appeal', 'project')

    action_to_serializers = {
        'create': UsersCreateUpdateSerializer,
        'update': UsersCreateUpdateSerializer,
    }

    def get_serializer_class(self):
        return self.action_to_serializers.get(
            self.action,
            self.serializer_class
        )


class UsersStatisticUserViewSet(StatisticUserMixin, viewsets.ModelViewSet):
    """
    Класс позволяет отображать статистичскую информацию о пользователях, без информации о событиях
    """

    permission_classes = (AllowAny,)
    queryset = Profile.objects.all()
    serializer_class = UsersStatisticSerializer
    filterset_fields = ('year_appeal', 'number_appeal', 'project')

    action_to_serializers = {
        'report': UsersStatisticSerializer
    }

    @action(detail=False)
    def report(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(
            position__in=(UserPosition.OPERATOR, UserPosition.SENIOR_OPERATOR)
        ).order_by('id').select_related('user', 'project')

        document_name = f'users_statistic-{timezone.now().strftime("%Y-%m-%d")}.docx'

        users_statistic_report(queryset, document_name)

        file_repository, _ = FileRepository.objects.get_or_create(
            name=document_name,
            defaults={'file': f'docs/{document_name}'})

        return Response({'url': file_repository.file.url})


class UserStatisticUserDetailAPIView(StatisticUserMixin, generics.RetrieveAPIView):
    """
    Класс позволяет отображать детализированную информацию о пользователе с информацией о событиях и показателях работы
    Отдельный сериализатор нужен для возможности фильтровать данные и выводить
    информацию о событиях (по ним и происходит фильтрация)
    """

    permission_classes = (AllowAny,)
    queryset = Profile.objects.all()
    serializer_class = UserStatisticDetailSerializer
    # TODO: Можно убрать после завершения
    filter_class = UserStatisticFilter

    # Пример запроса ?time_entry=2021-03-17&time_exit=2021-03-18

    # TODO: Можно убрать после завершения
    def filter_queryset(self, queryset):
        return queryset

    def get_queryset(self):
        return super().get_queryset().filter(user_id=self.kwargs['pk'])


class UserStatisticReportAPIView(StatisticUserMixin, generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    queryset = Profile.objects.all()
    serializer_class = UserStatisticDetailSerializer

    def get_queryset(self):
        return super().get_queryset().filter(user_id=self.kwargs['pk'])

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        user_id = self.kwargs['pk']

        document_name = f'user_statistic-{timezone.now().strftime("%Y-%m-%d")}-user_id-{user_id}.docx'

        user_statistic_report(serializer.data, user_id, document_name)

        file_repository, _ = FileRepository.objects.get_or_create(
            name=document_name,
            defaults={'file': f'docs/{document_name}'})

        return Response({'url': file_repository.file.url})


class UserProfileRetrieveAPIView(generics.RetrieveAPIView):
    """
    Класс позволяет отображать профиль пользователя.
    """

    permission_classes = (AllowAny,)
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)


class ProjectsStatisticUserViewSet(StatisticProjectMixin, viewsets.ModelViewSet):
    """
    Класс позволяет отображать статистику по проектам без событий (общая статистика)
    """

    permission_classes = (AllowAny,)
    queryset = Project.objects.all()
    serializer_class = ProjectsStatisticSerializer
    filterset_fields = ('name',)


class ProjectsStatisticDetailAPIView(StatisticProjectMixin, generics.ListAPIView):
    """
    Класс позволяет отображать детализированную информацию о проекте с информацией о событиях и показателях работы
    Отдельный сериализатор нужен для возможности фильтровать данные и выводить
    информацию о событиях (по ним и происходит фильтрация)
    """

    permission_classes = (AllowAny,)
    queryset = Project.objects.all()
    serializer_class = ProjectsStatisticDetailSerializer
    # TODO: Можно убрать после завершения
    filter_class = ProjectStatisticFilter

    # TODO: Можно убрать после завершения
    def filter_queryset(self, queryset):
        return queryset

    def get_queryset(self):
        return super().get_queryset().filter(id=self.kwargs['pk'])
