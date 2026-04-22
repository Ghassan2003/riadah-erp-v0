from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """واجهة إدارة سجلات التدقيق."""

    list_display = (
        'user', 'action', 'model_name', 'object_repr',
        'ip_address', 'created_at',
    )
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('user__username', 'model_name', 'object_repr', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = (
        'user', 'action', 'model_name', 'object_id', 'object_repr',
        'content_type', 'changes', 'old_values', 'new_values',
        'ip_address', 'user_agent', 'url_path', 'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True
