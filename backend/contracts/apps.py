"""
Contracts app configuration for ERP System.
Contracts Management module.
"""

from django.apps import AppConfig


class ContractsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contracts'
    verbose_name = 'إدارة العقود'
