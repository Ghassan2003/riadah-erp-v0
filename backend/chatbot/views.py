"""
API views for the chatbot module.
Handles REST endpoints for conversations and chat messages.
"""

import logging

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle

from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    ChatMessageSerializer,
    ChatResponseSerializer,
)
from .chat_service import process_chat_message

logger = logging.getLogger(__name__)


class ChatThrottle(UserRateThrottle):
    """Custom throttle for chat endpoint — 20 requests per minute."""

    rate = '20/min'


class ConversationListView(generics.ListCreateAPIView):
    """
    GET  /api/chatbot/conversations/  — List all conversations for the authenticated user.
    POST /api/chatbot/conversations/  — Create a new conversation.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on the HTTP method."""
        if self.request.method == 'POST':
            return ConversationCreateSerializer
        return ConversationListSerializer

    def get_serializer_context(self):
        """Pass the request context to the serializer."""
        return super().get_serializer_context()

    def get_queryset(self):
        """Return only active conversations belonging to the current user."""
        return Conversation.objects.filter(
            user=self.request.user,
            is_active=True,
        )

    def perform_create(self, serializer):
        """Create a new conversation associated with the current user."""
        serializer.save(user=self.request.user)
        logger.info(
            'New conversation created by user %s: %s',
            self.request.user.username,
            serializer.instance.title,
        )


class ConversationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/chatbot/conversations/<pk>/  — Retrieve conversation with messages.
    PATCH  /api/chatbot/conversations/<pk>/  — Update conversation title.
    DELETE /api/chatbot/conversations/<pk>/  — Soft-delete conversation (sets is_active=False).
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationDetailSerializer

    def get_queryset(self):
        """Return only conversations belonging to the current user."""
        return Conversation.objects.filter(
            user=self.request.user,
        )

    def perform_destroy(self, instance):
        """
        Soft-delete the conversation by setting is_active=False
        instead of permanently removing it from the database.
        """
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        logger.info(
            'Conversation %s soft-deleted by user %s',
            instance.id,
            self.request.user.username,
        )

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to return 200 OK with a confirmation message
        instead of the default 204 No Content.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'detail': 'تم حذف المحادثة بنجاح.'},
            status=status.HTTP_200_OK,
        )


class ChatMessageView(APIView):
    """
    POST /api/chatbot/chat/  — Send a message and receive an AI response.

    Request body:
        {
            "message": "user message text",
            "conversation_id": 123  (optional)
        }

    Response:
        {
            "response": "AI assistant response",
            "conversation_id": 123,
            "message_id": 456
        }
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ChatThrottle]

    def post(self, request, *args, **kwargs):
        """
        Process a chat message from the user and return an AI response.
        """
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message_text = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id')

        try:
            result = process_chat_message(
                user=request.user,
                message=message_text,
                conversation_id=conversation_id,
            )
        except (ValueError, RuntimeError, ImportError, ConnectionError) as exc:
            logger.error(
                'Chat processing error for user %s: %s',
                request.user.username,
                str(exc),
                exc_info=True,
            )
            return Response(
                {'detail': 'حدث خطأ أثناء معالجة رسالتك. يرجى المحاولة لاحقاً.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_serializer = ChatResponseSerializer(data=result)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
