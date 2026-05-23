"""
WebSocket consumer for the chatbot module.
Provides real-time bi-directional communication between the client and the AI assistant.
"""

import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class ChatbotConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that handles real-time chat messages.

    Protocol:
    - Client sends: {"message": "...", "conversation_id": 123 (optional)}
    - Server responds: {"response": "...", "conversation_id": 123, "message_id": 456}

    Authentication:
    - Uses Django Channels AuthMiddlewareStack (via scope['user']).
    - Anonymous users are rejected with close code 4001.
    """

    async def connect(self):
        """Accept the WebSocket connection if the user is authenticated."""
        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            logger.warning('Rejected anonymous WebSocket connection.')
            await self.close(code=4001)
            return

        self.user = user
        self.group_name = f'chatbot_user_{self.user.id}'

        # Join the user's personal chat group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        logger.info(
            'WebSocket connected for user %s (group: %s)',
            self.user.username,
            self.group_name,
        )

        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': 'مرحباً بك في المساعد الذكي لنظام ريادة ERP. كيف يمكنني مساعدتك؟',
        }, ensure_ascii=False))

    async def disconnect(self, close_code):
        """Remove the user from their chat group on disconnect."""
        group_name = getattr(self, 'group_name', None)
        if group_name:
            await self.channel_layer.group_discard(
                group_name,
                self.channel_name,
            )
            logger.info(
                'WebSocket disconnected for user %s (code: %s)',
                getattr(self, 'user', 'unknown'),
                close_code,
            )

    async def receive(self, text_data):
        """
        Handle incoming messages from the client.

        Expected JSON format:
        {
            "message": "user message text",
            "conversation_id": 123  (optional)
        }
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'صيغة الرسالة غير صالحة. يرجى إرسال JSON صحيح.',
            }, ensure_ascii=False))
            return

        message_text = data.get('message', '').strip()
        if not message_text:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'لا يمكن إرسال رسالة فارغة.',
            }, ensure_ascii=False))
            return

        conversation_id = data.get('conversation_id')

        try:
            # Process the message through the chat service (sync → async bridge)
            result = await self._process_message(message_text, conversation_id)

            # Send the response back to the client
            await self.send(text_data=json.dumps({
                'type': 'response',
                'response': result['response'],
                'conversation_id': result['conversation_id'],
                'message_id': result['message_id'],
            }, ensure_ascii=False))

        except Exception as exc:
            logger.error(
                'WebSocket chat error for user %s: %s',
                getattr(self, 'user', 'unknown'),
                str(exc),
                exc_info=True,
            )
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'حدث خطأ أثناء معالجة رسالتك. يرجى المحاولة لاحقاً.',
            }, ensure_ascii=False))

    @database_sync_to_async
    def _process_message(self, message_text, conversation_id):
        """
        Bridge to call the synchronous process_chat_message from the chat_service.
        Wrapped with database_sync_to_async to avoid blocking the event loop.
        """
        from .chat_service import process_chat_message

        return process_chat_message(
            user=self.user,
            message=message_text,
            conversation_id=conversation_id,
        )

    async def chat_message(self, event):
        """
        Handler for messages sent via the channel layer (group messages).
        Allows sending messages to the user from outside the consumer.
        """
        await self.send(text_data=json.dumps({
            'type': event.get('type', 'notification'),
            'message': event.get('message', ''),
        }, ensure_ascii=False))
