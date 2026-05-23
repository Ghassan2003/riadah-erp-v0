"""
WebSocket URL routing for the notifications app - ERP System.
Maps WebSocket paths to their corresponding consumer classes.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'^ws/notifications/$',
        consumers.NotificationConsumer.as_asgi(),
        name='ws-notifications',
    ),
]
