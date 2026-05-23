"""
WebSocket consumers for real-time notifications - ERP System.
Handles WebSocket connections per user and delivers notifications
as they are created via Django's channel layer.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that delivers real-time notifications to authenticated users.

    Each user connects to a personal group (notifications_{user_id}).
    When a new notification is created for that user, it is pushed
    to the group and delivered to all active WebSocket connections.
    """

    async def connect(self):
        """Accept the WebSocket connection for authenticated users only."""
        # Reject anonymous users immediately
        if self.scope["user"].is_anonymous:
            await self.close(code=4001)
            return

        self.user = self.scope["user"]
        self.group_name = f'notifications_{self.user.id}'

        # Join the user's personal notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Accept the connection
        await self.accept()

        logger.info(
            "WebSocket connected for user %s (id=%s)",
            self.user.username, self.user.id
        )

        # Send unread count on connect so the client can sync immediately
        unread_count = await self._get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': self.user.id,
            'unread_count': unread_count,
        }))

    async def disconnect(self, close_code):
        """Remove the user from the notification group on disconnect."""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(
                "WebSocket disconnected for user %s (code=%s)",
                getattr(self, 'user', 'unknown'), close_code
            )

    async def send_notification(self, event):
        """
        Receive notification data from the channel layer and forward
        it to the WebSocket client as JSON.
        """
        await self.send(text_data=json.dumps(event['data']))

    async def notify_unread_count(self, event):
        """
        Receive unread count updates from the channel layer and forward
        them to the WebSocket client.
        """
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update',
            'unread_count': event['count'],
        }))

    @database_sync_to_async
    def _get_unread_count(self):
        """Fetch the user's unread notification count from the database."""
        from .models import Notification
        return Notification.objects.filter(
            recipient_id=self.user.id,
            is_read=False,
        ).count()
