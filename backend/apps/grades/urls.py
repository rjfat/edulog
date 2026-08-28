from django.urls import path

from . import views

urlpatterns = [
    path('', views.grade_list, name='grade_list'),
    path('new/', views.grade_add, name='grade_add'),
    path('report/', views.grade_report, name='grade_report'),
    path('<int:pk>/edit/', views.grade_edit, name='grade_edit'),
    path('<int:pk>/delete/', views.grade_delete, name='grade_delete'),
]
