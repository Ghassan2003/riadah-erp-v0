from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'المستخدمون'

    def ready(self):
        """تسجيل الإشارات عند جاهزية التطبيق."""
        import users.signals  # noqa: F401
