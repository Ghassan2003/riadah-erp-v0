"""
Warehouse app configuration for ERP System.
Multi-Warehouse Management module.
"""

from django.apps import AppConfig


class WarehouseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'warehouse'
    verbose_name = 'إدارة المستودعات'
