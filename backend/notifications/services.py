"""
Notification push services - ERP System.
Provides helper functions to push notifications to users
in real-time via Django Channels' channel layer.
"""

import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def push_notification(user_id, notification_data):
    """
    Push a notification to a specific user via WebSocket.

    Args:
        user_id: The ID of the recipient user.
        notification_data: A dict containing notification payload.
            Expected keys: id, title, message, notification_type,
            link, priority, created_at, is_read, etc.
    """
    try:
        channel_layer = get_channel_layer()
        group_name = f'notifications_{user_id}'
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification',
                'data': notification_data,
            }
        )
        logger.debug(
            "Pushed notification %s to user %s via WebSocket",
            notification_data.get('id', '?'),
            user_id,
        )
    except Exception:
        logger.exception(
            "Failed to push notification to user %s via channel layer",
            user_id,
        )


def push_unread_count(user_id, count):
    """
    Push an updated unread count to a specific user via WebSocket.

    Args:
        user_id: The ID of the recipient user.
        count: The new unread notification count.
    """
    try:
        channel_layer = get_channel_layer()
        group_name = f'notifications_{user_id}'
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notify_unread_count',
                'count': count,
            }
        )
    except Exception:
        logger.exception(
            "Failed to push unread count to user %s via channel layer",
            user_id,
        )


def serialize_notification(notification):
    """
    Serialize a Notification model instance into a JSON-serializable dict
    suitable for sending over WebSocket.

    Args:
        notification: A Notification model instance.

    Returns:
        A dict with notification data.
    """
    from .models import Notification
    data = {
        'id': notification.id,
        'title': notification.title,
        'message': notification.message,
        'notification_type': notification.notification_type,
        'link': notification.link or '',
        'priority': notification.priority,
        'is_read': notification.is_read,
        'created_at': notification.created_at.isoformat(),
    }
    if notification.sender:
        data['sender'] = {
            'id': notification.sender.id,
            'username': notification.sender.username,
            'full_name': getattr(notification.sender, 'full_name', notification.sender.username),
        }
    if notification.content_object:
        data['content_object'] = {
            'type': notification.content_type.model,
            'id': notification.object_id,
        }
    return data
