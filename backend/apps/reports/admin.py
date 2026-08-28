from django.contrib import admin

from .models import AuditLog, SchoolSettings


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'action', 'user', 'ip_address']
    list_filter = ['action', 'created_at']
    search_fields = ['details', 'user__username', 'user__email']
    readonly_fields = ['user', 'action', 'details', 'ip_address', 'created_at']


@admin.register(SchoolSettings)
class SchoolSettingsAdmin(admin.ModelAdmin):
    list_display = ['school_name', 'academic_year', 'term_label', 'updated_at']