from django.apps import AppConfig


class InternalauditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'internalaudit'
    verbose_name = 'التدقيق الداخلي'
