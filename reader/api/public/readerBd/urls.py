from django.urls import path
from rest_framework import routers

from .views import ControlTimeViewSet, ControlTimeTodayList, DayViewSet, ScheduleDutyViewSet, ListEventsViewSet, \
    EventViewSet

app_name = 'readerBd'

router = routers.SimpleRouter()

router.register('list_events', ListEventsViewSet, basename='list_events')
router.register('events', EventViewSet, basename='events')
router.register('control_times', ControlTimeViewSet, basename='control_times')
router.register('days', DayViewSet, basename='days')
router.register('schedule_duty', ScheduleDutyViewSet, basename='schedule_duty')

urlpatterns = [
    path('control_times/today/', ControlTimeTodayList.as_view(), name='control_time_today'),
]

urlpatterns += router.urls
