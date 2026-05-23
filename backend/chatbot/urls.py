"""
URL configuration for the chatbot module.
Maps REST API endpoints to their corresponding views.
"""

from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # List all conversations / Create a new conversation
    path(
        'conversations/',
        views.ConversationListView.as_view(),
        name='conversation-list-create',
    ),
    # Retrieve, update, or soft-delete a specific conversation
    path(
        'conversations/<int:pk>/',
        views.ConversationDetailView.as_view(),
        name='conversation-detail',
    ),
    # Send a message and get AI response
    path(
        'chat/',
        views.ChatMessageView.as_view(),
        name='chat-message',
    ),
]
