from django.urls import path

from . import views

urlpatterns = [
    path('', views.report_index, name='report_index'),
    path('student/', views.student_report, name='report_student'),
    path('course/', views.course_report, name='report_course'),
    path('attendance/', views.attendance_report, name='report_attendance'),
    path('settings/', views.settings_view, name='settings'),
    path('audit/', views.audit_logs, name='audit_logs'),
]