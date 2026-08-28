from django.urls import path

from . import views

urlpatterns = [
    path('', views.message_inbox, name='message_inbox'),
    path('sent/', views.message_sent, name='message_sent'),
    path('compose/', views.message_compose, name='message_compose'),
    path('<int:pk>/', views.message_detail, name='message_detail'),
]