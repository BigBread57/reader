from django.urls import path
from rest_framework import routers

from .views import UsersStatisticUserViewSet, UserStatisticUserDetailAPIView, UserProfileRetrieveAPIView, \
    UsersViewSet, ProjectsStatisticUserViewSet, ProjectsStatisticDetailAPIView, UserStatisticReportAPIView, \
    ProjectsStatisticReportAPIView

app_name = 'accountBd'

router = routers.SimpleRouter()

router.register('users_statistic', UsersStatisticUserViewSet, basename='users_statistic')
router.register('projects_statistic', ProjectsStatisticUserViewSet, basename='projects_statistic')
router.register('users', UsersViewSet, basename='users')

urlpatterns = [
    path('users_statistic/<int:pk>/details/', UserStatisticUserDetailAPIView.as_view(), name='user_statistic'),
    path('users_statistic/<int:pk>/details/report/', UserStatisticReportAPIView.as_view(),
         name='user_statistic_report'),
    path('projects_statistic/<int:pk>/details/', ProjectsStatisticDetailAPIView.as_view(), name='project_statistic'),
    path('projects_statistic/<int:pk>/details/report/', ProjectsStatisticReportAPIView.as_view(),
         name='project_statistic_report'),
    path('profile/', UserProfileRetrieveAPIView.as_view(), name='user_profile'),
]

urlpatterns += router.urls
