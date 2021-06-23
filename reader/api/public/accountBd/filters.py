import django_filters

from accountBd.models import Profile, Project


class UserStatisticFilter(django_filters.FilterSet):
    # TODO: Можно убрать после завершения
    time_entry = django_filters.DateFilter(label="Дата входа",
                                           field_name='user__days__date', lookup_expr='gte')
    time_exit = django_filters.DateFilter(label="Дата выхода",
                                          field_name='user__days__date', lookup_expr='lte')

    class Meta:
        model = Profile
        fields = ['time_entry', 'time_exit']


class ProjectStatisticFilter(django_filters.FilterSet):
    # TODO: Можно убрать после завершения
    time_entry = django_filters.DateFilter(label="Дата входа",
                                           field_name='days__date', lookup_expr='gte')
    time_exit = django_filters.DateFilter(label="Дата выхода",
                                          field_name='days__date', lookup_expr='lte')

    class Meta:
        model = Project
        fields = ['time_entry', 'time_exit']
