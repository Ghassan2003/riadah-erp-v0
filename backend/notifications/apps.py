"""
تهيئة تطبيق الإشعارات لنظام ERP.
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'الإشعارات'

    def ready(self):
        """Import signals so the post_save receiver is registered."""
        import notifications.signals  # noqa: F401
