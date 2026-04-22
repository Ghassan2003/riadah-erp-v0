"""
المسلسلات لنظام الإشعارات - نظام ERP.
تحويل بيانات الإشعارات إلى صيغة JSON للإرسال عبر API.
"""

from rest_framework import serializers
from .models import Notification


class NotificationListSerializer(serializers.ModelSerializer):
    """مسلسل عرض قائمة الإشعارات."""

    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display', read_only=True
    )
    sender_name = serializers.SerializerMethodField()

    def get_sender_name(self, obj):
        if obj.sender:
            return obj.sender.get_full_name() or obj.sender.username
        return None

    class Meta:
        model = Notification
        fields = (
            'id', 'title', 'message', 'notification_type',
            'notification_type_display', 'priority', 'priority_display',
            'link', 'is_read', 'created_at', 'sender_name',
        )
        read_only_fields = ('id', 'created_at')


class NotificationDetailSerializer(NotificationListSerializer):
    """مسلسل عرض تفاصيل إشعار."""

    class Meta(NotificationListSerializer.Meta):
        pass


class _LazyUserPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """حقل مرجعي أساسي مع استيراد متأخر لنموذج المستخدم."""

    def get_queryset(self):
        from users.models import User
        return User.objects.all()


class NotificationCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء إشعار (للاستخدام الإداري)."""
    recipient_id = _LazyUserPrimaryKeyRelatedField(
        source='recipient', write_only=True
    )
    sender_id = _LazyUserPrimaryKeyRelatedField(
        source='sender', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Notification
        fields = ('recipient_id', 'sender_id', 'title', 'message',
                  'notification_type', 'priority', 'link', 'expires_at')
        read_only_fields = ('id', 'created_at', 'is_read')
