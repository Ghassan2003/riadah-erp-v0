"""
Admin configuration for the Attachment model.
"""

from django.contrib import admin
from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """Custom admin interface for Attachment."""

    list_display = (
        'file_name', 'file_type', 'file_size', 'content_type',
        'object_id', 'uploaded_by', 'is_public', 'created_at',
    )
    list_filter = ('file_type', 'is_public', 'category', 'created_at')
    search_fields = ('file_name', 'description', 'uploaded_by__username')
    ordering = ('-created_at',)
    readonly_fields = ('file_size', 'file_type', 'file_name', 'created_at')

    fieldsets = (
        ('معلومات الملف', {
            'fields': ('file', 'file_name', 'file_size', 'file_type')
        }),
        ('الربط بكائن', {
            'fields': ('content_type', 'object_id'),
        }),
        ('معلومات إضافية', {
            'fields': ('description', 'category', 'is_public', 'uploaded_by')
        }),
        ('التواريخ', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
