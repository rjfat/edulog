from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'subject', 'read', 'created_at']
    list_filter = ['read', 'created_at']
    search_fields = ['subject', 'body', 'sender__username', 'receiver__username']
    autocomplete_fields = ['sender', 'receiver']