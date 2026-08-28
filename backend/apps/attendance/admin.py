from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'date', 'status']
    list_filter = ['course', 'status', 'date']
    search_fields = ['student__username', 'student__email', 'course__code']
    autocomplete_fields = ['student', 'course']
