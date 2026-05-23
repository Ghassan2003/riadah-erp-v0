"""
تهيئة لوحة الإدارة لنظام الإشعارات - نظام ERP.
"""

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username')
    ordering = ('-created_at',)
    list_editable = ('is_read',)
    readonly_fields = ('created_at',)
