from rest_framework import serializers
from .models import AuditLog


class AuditLogListSerializer(serializers.ModelSerializer):
    """Serializer for listing audit log entries."""

    action_display = serializers.CharField(source='get_action_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, default='نظام')

    class Meta:
        model = AuditLog
        fields = (
            'id', 'user', 'username', 'action', 'action_display',
            'model_name', 'object_id', 'object_repr',
            'old_values', 'new_values', 'changes',
            'ip_address', 'url_path', 'created_at',
        )
        read_only_fields = ('id', 'created_at')
