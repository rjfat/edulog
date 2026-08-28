from django.contrib import admin

from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'target_role', 'created_at']
    list_filter = ['target_role', 'created_at']
    search_fields = ['title', 'content', 'author__username', 'author__email']
    autocomplete_fields = ['author']