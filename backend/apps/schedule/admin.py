from django.contrib import admin

from .models import Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['course', 'get_day_of_week_display', 'start_time', 'end_time', 'room']
    list_filter = ['day_of_week', 'room']
    search_fields = ['course__code', 'course__name', 'room']
    autocomplete_fields = ['course']