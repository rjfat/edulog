"""EduLog URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard'), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('courses/', include('apps.courses.urls')),
    path('grades/', include('apps.grades.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('announcements/', include('apps.announcements.urls')),
    path('messages/', include('apps.messaging.urls')),
    path('schedule/', include('apps.schedule.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
