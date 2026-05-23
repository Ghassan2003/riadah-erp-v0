"""
WebSocket URL routing for the chatbot module - RIADAH ERP.
Maps WebSocket paths to their corresponding consumer classes.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'^ws/chatbot/$',
        consumers.ChatbotConsumer.as_asgi(),
        name='ws-chatbot',
    ),
]
