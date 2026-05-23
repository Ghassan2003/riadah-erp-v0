"""App configuration for startup_finance module."""

from django.apps import AppConfig


class StartupFinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'startup_finance'
    verbose_name = 'تمويل الشركات الناشئة'

    def ready(self):
        """تسجيل الإشارات والجدولة عند جاهزية التطبيق."""
        import startup_finance.signals  # noqa: F401
