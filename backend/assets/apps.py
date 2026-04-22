"""
Assets app configuration for ERP System.
Fixed Assets Management module.
"""

from django.apps import AppConfig


class AssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assets'
    verbose_name = 'الأصول الثابتة'
