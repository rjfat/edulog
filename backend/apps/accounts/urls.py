from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.EduLogLoginView.as_view(), name='login'),
    path('logout/', views.EduLogLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path(
        'password/change/',
        views.EduLogPasswordChangeView.as_view(),
        name='password_change',
    ),
    path(
        'password/reset/',
        views.EduLogPasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        'password/reset/sent/',
        views.EduLogPasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    path(
        'password/reset/<uidb64>/<token>/',
        views.EduLogPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'password/reset/done/',
        views.EduLogPasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
    path('users/', views.user_list, name='user_list'),
    path('users/new/', views.user_create, name='user_create'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
]
