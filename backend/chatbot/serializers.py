"""
Django REST Framework serializers for the chatbot module.
Handles data validation and transformation for conversation and message APIs.
"""

from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for individual chat messages."""

    class Meta:
        model = Message
        fields = ('id', 'role', 'content', 'created_at')
        read_only_fields = ('id', 'role', 'content', 'created_at')


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for listing conversations (summary view)."""

    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ('id', 'title', 'created_at', 'message_count')

    def get_message_count(self, obj):
        """Return the total number of messages in the conversation."""
        return obj.messages.count()


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer for conversation detail view with all messages."""

    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ('id', 'title', 'is_active', 'created_at', 'messages')
        read_only_fields = ('id', 'created_at')


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new conversation."""

    class Meta:
        model = Conversation
        fields = ('title',)

    def validate_title(self, value):
        """Validate the title field."""
        if not value or not value.strip():
            return 'محادثة جديدة'
        return value.strip()


class ChatMessageSerializer(serializers.Serializer):
    """Serializer for incoming chat messages from the user."""

    message = serializers.CharField(
        max_length=4000,
        write_only=True,
        help_text='نص الرسالة من المستخدم',
    )
    conversation_id = serializers.IntegerField(
        required=False,
        write_only=True,
        allow_null=True,
        help_text='معرّف المحادثة (اختياري)',
    )

    def validate_message(self, value):
        """Ensure the message is not empty."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError('لا يمكن إرسال رسالة فارغة.')
        return value


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for the chatbot response."""

    response = serializers.CharField(help_text='رد المساعد الذكي')
    conversation_id = serializers.IntegerField(help_text='معرّف المحادثة')
    message_id = serializers.IntegerField(help_text='معرّف رسالة المساعد')
