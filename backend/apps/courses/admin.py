from django.contrib import admin

from .models import Course, Enrollment


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    autocomplete_fields = ['student']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'teacher', 'created_at']
    list_filter = ['teacher']
    search_fields = ['code', 'name']
    autocomplete_fields = ['teacher']
    inlines = [EnrollmentInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'enrolled_at']
    list_filter = ['course']
    search_fields = ['student__username', 'student__email', 'course__code', 'course__name']
    autocomplete_fields = ['student', 'course']
