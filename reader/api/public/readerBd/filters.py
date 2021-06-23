import django_filters

from readerBd.models import ControlTime


class ControlTimeFilter(django_filters.FilterSet):
    time_entry = django_filters.DateTimeFilter(field_name='time_entry', lookup_expr='gte')
    time_exit = django_filters.DateTimeFilter(field_name='time_exit', lookup_expr='lte')

    class Meta:
        model = ControlTime
        fields = ['day', 'time_entry', 'time_exit']
