"""
Chatbot App Configuration for RIADAH ERP System.
Provides an AI-powered intelligent assistant for ERP users.
"""

from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
    verbose_name = 'المساعد الذكي'

    def ready(self):
        """Initialize chatbot services when the app is ready."""
        import chatbot.signals  # noqa: F401
