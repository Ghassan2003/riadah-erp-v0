"""
Django Admin configuration for chatbot models.
"""

from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin configuration for Conversation model."""

    list_display = (
        'id',
        'title',
        'user',
        'is_active',
        'message_count',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'is_active',
        'created_at',
    )
    search_fields = (
        'title',
        'user__username',
        'user__email',
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active',)

    def message_count(self, obj):
        """Display the number of messages in this conversation."""
        return obj.messages.count()

    message_count.short_description = 'عدد الرسائل'
    message_count.admin_order_field = 'messages__count'

    def get_queryset(self, request):
        """Annotate queryset with message count for ordering."""
        from django.db.models import Count
        qs = super().get_queryset(request)
        return qs.annotate(_message_count=Count('messages'))

    message_count.admin_order_field = '_message_count'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for Message model."""

    list_display = (
        'id',
        'conversation',
        'role',
        'content_preview',
        'created_at',
    )
    list_filter = (
        'role',
        'created_at',
    )
    search_fields = (
        'content',
        'conversation__title',
        'conversation__user__username',
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    def content_preview(self, obj):
        """Display the first 50 characters of the message content."""
        preview = obj.content[:50]
        if len(obj.content) > 50:
            preview += '...'
        return preview

    content_preview.short_description = 'محتوى الرسالة'
