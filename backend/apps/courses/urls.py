from django.urls import path

from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('new/', views.course_create, name='course_create'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('<int:pk>/delete/', views.course_delete, name='course_delete'),
    path('<int:pk>/roster/', views.course_roster, name='course_roster'),
    path('<int:pk>/roster/enroll/', views.course_enroll, name='course_enroll'),
    path('<int:pk>/roster/<int:student_pk>/remove/', views.course_unenroll, name='course_unenroll'),
    path('<int:pk>/join/', views.course_join, name='course_join'),
    path('<int:pk>/leave/', views.course_leave, name='course_leave'),
]
