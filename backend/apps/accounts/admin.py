from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class EduLogUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']

    fieldsets = UserAdmin.fieldsets + (
        (
            'EduLog profile',
            {'fields': ('role', 'phone', 'address', 'profile_picture', 'created_at', 'updated_at')},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('EduLog profile', {'fields': ('email', 'first_name', 'last_name', 'role')}),
    )
