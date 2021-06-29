from rest_framework import permissions

from accountBd.collections import UserPosition


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Разрешение на редактирование/добавление/удаление информации о пользователе
    """

    def has_object_permission(self, request, view, obj):
        if permissions.SAFE_METHODS:

            return True

        if request.method == 'PUT' and request.user == obj.user:

            return True

        if request.user.is_staff or request.user.profile.position in (UserPosition.DUTY,
                                                                      UserPosition.LEADER_LABORATORY,
                                                                      UserPosition.ENGINEER):

            return True


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение на редактирование любой статистической информации
    """

    def has_object_permission(self, request, view, obj):

        if permissions.SAFE_METHODS:

            return True

        if request.user.profile.position == UserPosition.LEADER_LABORATORY or request.user.is_staff:

            return True


class IsReport(permissions.BasePermission):
    """
    Разрешение на скачивание статистических отчетов
    """

    def has_object_permission(self, request, view, obj):

        if request.user.profile.position == UserPosition.LEADER_LABORATORY or request.user.is_staff:
            return True
