from rest_framework import permissions

from accountBd.collections import UserPosition


class IsPersonalOrReadOnly(permissions.BasePermission):
    """
    Разрешение на редактирование/добавление/удаление информации о пользователе
    """

    def has_object_permission(self, request, view, obj):
        if permissions.SAFE_METHODS:

            return True

        if request.user.is_staff or request.user.profile.position in (UserPosition.DUTY,
                                                                      UserPosition.LEADER_LABORATORY,
                                                                      UserPosition.ENGINEER):

            return True
