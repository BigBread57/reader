from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _
from .models import Profile, Project, User, FileRepository


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Определение модели администратора для пользовательской модели пользователя с полем электронной почты."""
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('last_name', 'first_name', 'third_name', 'email')}),
        (_('Permissions'), {'fields': ('code', 'is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'code'),
        }),
    )


admin.site.register(Profile)
admin.site.register(Project)
admin.site.register(FileRepository)
