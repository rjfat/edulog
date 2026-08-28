from django.contrib import admin

from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'assignment_name', 'grade', 'percentage', 'created_at']
    list_filter = ['course', 'grade']
    search_fields = ['student__username', 'student__email', 'course__code', 'assignment_name']
    autocomplete_fields = ['student', 'course']
